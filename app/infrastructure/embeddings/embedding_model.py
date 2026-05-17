from __future__ import annotations

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    settings = get_settings()
    return SentenceTransformer(settings.embedding_model_name)


def _expected_dimensions() -> int:
    return get_settings().vector_dimensions


def embed_text(text: str) -> list[float]:
    """Gera o vetor de embedding para um único texto."""
    if not text.strip():
        raise ValueError("texto vazio não pode ser convertido em embedding")
    model = _load_model()
    vector = model.encode(
        text,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return _to_list_and_validate(vector)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Gera embeddings em lote (ordem preservada)."""
    if not texts:
        return []
    if any(not t.strip() for t in texts):
        raise ValueError("nenhum item pode ser texto vazio")
    model = _load_model()
    matrix = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    rows: list[list[float]] = []
    for row in np.atleast_2d(matrix):
        rows.append(_to_list_and_validate(row))
    return rows


def _to_list_and_validate(vector: np.ndarray) -> list[float]:
    flat = np.asarray(vector, dtype=np.float32).ravel()
    expected = _expected_dimensions()
    if flat.shape[0] != expected:
        raise RuntimeError(
            f"dimensão do embedding ({flat.shape[0]}) difere de vector_dimensions ({expected}); "
            "ajuste VECTOR_DIMENSIONS ou o modelo em configuração."
        )
    return flat.tolist()
