from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.infrastructure.db.models.document import Document


@dataclass(frozen=True)
class SimilarDocument:
    """Resultado de busca por similaridade (operador `<=>` do pgvector)."""

    id: int
    content: str
    source: str
    # Distância cosseno; valores menores = mais similar (com normalize_embeddings no encoder).
    cosine_distance: float


class PgVectorStore:
    """Operações de persistência e consulta vetorial na tabela `documents`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def insert_document(
        self,
        *,
        content: str,
        source: str,
        embedding: list[float],
        content_hash: str | None = None,
        source_url: str | None = None,
        source_topic: str | None = None,
        corpus_version: str | None = None,
    ) -> Document:
        """Insere um documento com embedding já calculado."""
        self._validate_embedding(embedding)
        row = Document(
            content=content,
            source=source,
            embedding=embedding,
            content_hash=content_hash,
            source_url=source_url,
            source_topic=source_topic,
            corpus_version=corpus_version,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def search_similar_by_embedding(
        self,
        query_embedding: list[float],
        *,
        top_k: int,
        corpus_versions: tuple[str, ...] | None = None,
    ) -> list[SimilarDocument]:
        """
        Retorna os `top_k` documentos mais próximos por distância cosseno ao embedding da consulta.
        Requer vetores com a mesma dimensão configurada em `vector_dimensions`.
        """
        if top_k < 1:
            raise ValueError("top_k deve ser >= 1")
        self._validate_embedding(query_embedding)

        distance_expr = Document.embedding.cosine_distance(query_embedding)
        stmt = select(Document, distance_expr.label("distance"))
        if corpus_versions:
            stmt = stmt.where(Document.corpus_version.in_(corpus_versions))
        stmt = stmt.order_by(distance_expr).limit(top_k)

        result = self._session.execute(stmt).all()
        out: list[SimilarDocument] = []
        for doc, dist in result:
            out.append(
                SimilarDocument(
                    id=doc.id,
                    content=doc.content,
                    source=doc.source,
                    cosine_distance=float(dist),
                )
            )
        return out

    def _validate_embedding(self, embedding: list[float]) -> None:
        expected = get_settings().vector_dimensions
        if len(embedding) != expected:
            raise ValueError(
                f"embedding com {len(embedding)} dimensões; esperado {expected}"
            )
