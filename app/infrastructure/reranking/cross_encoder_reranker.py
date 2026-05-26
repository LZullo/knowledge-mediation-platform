"""Reranking local com sentence-transformers CrossEncoder."""

from __future__ import annotations

from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.core.config import get_settings


@lru_cache(maxsize=1)
def _load_cross_encoder() -> CrossEncoder:
    settings = get_settings()
    return CrossEncoder(settings.rerank_model_name)


def score_question_passages(question: str, passages: list[str]) -> list[float]:
    """
    Pontua pares (pergunta, passagem). Scores maiores = mais relevantes.
    """
    if not passages:
        return []
    model = _load_cross_encoder()
    pairs = [[question, passage] for passage in passages]
    raw = model.predict(pairs)
    return [float(s) for s in raw]
