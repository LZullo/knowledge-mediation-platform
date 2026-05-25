"""Estratégias de recuperação de documentos."""

from app.application.strategies.retrieval.pgvector import (
    NoRetrievalStrategy,
    PgVectorRetrievalStrategy,
    RetrievalStrategy,
)
from app.application.strategies.retrieval.rerank_pgvector_strategy import (
    RerankPgVectorRetrievalStrategy,
)

__all__ = [
    "RetrievalStrategy",
    "PgVectorRetrievalStrategy",
    "NoRetrievalStrategy",
    "RerankPgVectorRetrievalStrategy",
]
