"""Serviços de aplicação (sem reexportar strategies — evita import circular na indexação)."""

from app.application.services.indexing_pipeline import IndexingReport, index_txt_directory
from app.application.services.rag_pipeline import (
    RAGPipelineResult,
    cosine_distance_to_similarity,
    run_rag_pipeline,
)
from app.application.services.vector_context import (
    IndexDocumentItem,
    index_document,
    index_documents,
    retrieve_similar_documents,
)

__all__ = [
    "IndexDocumentItem",
    "IndexingReport",
    "RAGPipelineResult",
    "cosine_distance_to_similarity",
    "index_document",
    "index_documents",
    "index_txt_directory",
    "retrieve_similar_documents",
    "run_rag_pipeline",
]
