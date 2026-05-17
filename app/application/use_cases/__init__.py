"""Casos de uso (interactors)."""

from app.application.use_cases.execute_rag import (
    RAGScenario,
    ExecuteRAGInput,
    RAG_BASIC_TOP_K,
    RAG_OPTIMIZED_DEFAULT_TOP_K,
    execute_rag,
)

__all__ = [
    "RAGScenario",
    "ExecuteRAGInput",
    "RAG_BASIC_TOP_K",
    "RAG_OPTIMIZED_DEFAULT_TOP_K",
    "execute_rag",
]
