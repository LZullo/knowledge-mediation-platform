"""Estratégias plugáveis para o pipeline RAG e experimentos."""

from app.application.strategies.generation import (
    GenerationStrategy,
    OpenAIGenerationStrategy,
)
from app.application.strategies.prompt import (
    DefaultPromptStrategy,
    DirectQuestionPromptStrategy,
    PromptStrategy,
    RestrictiveRagPromptStrategy,
)
from app.application.strategies.retrieval import (
    NoRetrievalStrategy,
    PgVectorRetrievalStrategy,
    RerankPgVectorRetrievalStrategy,
    RetrievalStrategy,
)

__all__ = [
    "GenerationStrategy",
    "OpenAIGenerationStrategy",
    "PromptStrategy",
    "DefaultPromptStrategy",
    "DirectQuestionPromptStrategy",
    "RestrictiveRagPromptStrategy",
    "RetrievalStrategy",
    "PgVectorRetrievalStrategy",
    "RerankPgVectorRetrievalStrategy",
    "NoRetrievalStrategy",
]
