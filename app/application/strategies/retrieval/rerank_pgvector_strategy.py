"""
Recuperação vetorial expandida + reranking semântico (CrossEncoder).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.infrastructure.embeddings import embed_text
from app.infrastructure.reranking import score_question_passages
from app.infrastructure.vectorstore import PgVectorStore, SimilarDocument

logger = logging.getLogger(__name__)


def _cosine_distance_to_similarity(cosine_distance: float) -> float:
    score = 1.0 - (cosine_distance / 2.0)
    if score < 0.0:
        return 0.0
    if score > 1.0:
        return 1.0
    return score


def _rerank_score_to_cosine_distance(
    score: float,
    *,
    min_score: float,
    max_score: float,
) -> float:
    """Mapeia score do cross-encoder para distância compatível com o pipeline RAG."""
    if max_score <= min_score:
        return 0.0
    normalized = (score - min_score) / (max_score - min_score)
    return 2.0 * (1.0 - normalized)


@dataclass
class RerankPgVectorRetrievalStrategy:
    """
    Fluxo: pgvector(top_k_expandido) → CrossEncoder → top_k final.

    `rerank_top_k` = candidatos iniciais do pgvector.
    `top_k` em `retrieve()` = quantidade final devolvida ao pipeline.
    """

    rerank_top_k: int = 10
    score_threshold: float | None = None

    def __post_init__(self) -> None:
        if self.rerank_top_k < 1:
            raise ValueError("rerank_top_k deve ser >= 1")

    def retrieve(self, session: Session, question: str, top_k: int) -> list[SimilarDocument]:
        if top_k < 1:
            raise ValueError("top_k deve ser >= 1")

        expanded_k = max(self.rerank_top_k, top_k)
        query_embedding = embed_text(question)
        store = PgVectorStore(session)
        candidates = store.search_similar_by_embedding(query_embedding, top_k=expanded_k)

        logger.info(
            "Rerank: pgvector recuperou %s chunks (expandido=%s, final=%s)",
            len(candidates),
            expanded_k,
            top_k,
        )

        if not candidates:
            return []

        for doc in candidates:
            sim = _cosine_distance_to_similarity(doc.cosine_distance)
            logger.info(
                "Rerank antes: id=%s source=%s dist=%.4f sim=%.4f",
                doc.id,
                doc.source,
                doc.cosine_distance,
                sim,
            )

        passages = [doc.content for doc in candidates]
        rerank_scores = score_question_passages(question, passages)

        scored: list[tuple[SimilarDocument, float]] = list(zip(candidates, rerank_scores, strict=True))
        scored.sort(key=lambda item: item[1], reverse=True)

        min_score = min(rerank_scores)
        max_score = max(rerank_scores)

        kept: list[tuple[SimilarDocument, float]] = []
        discarded_threshold = 0
        for doc, score in scored:
            if self.score_threshold is not None and score < self.score_threshold:
                discarded_threshold += 1
                logger.info(
                    "Rerank descartado (threshold=%.4f): id=%s score=%.4f",
                    self.score_threshold,
                    doc.id,
                    score,
                )
                continue
            kept.append((doc, score))

        if discarded_threshold:
            logger.info(
                "Rerank: %s chunks descartados por score_threshold",
                discarded_threshold,
            )

        final_pairs = kept[:top_k]
        discarded_rank = len(kept) - len(final_pairs)
        if discarded_rank > 0:
            logger.info("Rerank: %s chunks descartados após cortar top_k=%s", discarded_rank, top_k)

        out: list[SimilarDocument] = []
        for doc, score in final_pairs:
            dist = _rerank_score_to_cosine_distance(
                score,
                min_score=min_score,
                max_score=max_score,
            )
            sim = _cosine_distance_to_similarity(dist)
            logger.info(
                "Rerank depois: id=%s score=%.4f dist=%.4f sim=%.4f",
                doc.id,
                score,
                dist,
                sim,
            )
            out.append(
                SimilarDocument(
                    id=doc.id,
                    content=doc.content,
                    source=doc.source,
                    cosine_distance=dist,
                )
            )

        return out
