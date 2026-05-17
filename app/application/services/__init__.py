"""Serviços de aplicação."""

from app.application.strategies import (
    DefaultPromptStrategy,
    GenerationStrategy,
    OpenAIGenerationStrategy,
    PgVectorRetrievalStrategy,
    PromptStrategy,
    RetrievalStrategy,
)
from app.application.services.rag_pipeline import (
    RAGPipelineResult,
    cosine_distance_to_similarity,
    run_rag_pipeline,
)
from app.application.services.indexing_pipeline import (
    IndexingReport,
    index_txt_directory,
)
from app.application.services.vector_context import (
    index_document,
    index_documents,
    retrieve_similar_documents,
)

__all__ = [
    "RAGPipelineResult",
    "cosine_distance_to_similarity",
    "run_rag_pipeline",
    "DefaultPromptStrategy",
    "GenerationStrategy",
    "OpenAIGenerationStrategy",
    "PgVectorRetrievalStrategy",
    "PromptStrategy",
    "RetrievalStrategy",
    "index_document",
    "index_documents",
    "retrieve_similar_documents",
    "IndexingReport",
    "index_txt_directory",
]
