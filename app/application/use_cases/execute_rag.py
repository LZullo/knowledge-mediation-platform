"""
Caso de uso: executa o fluxo RAG (ou LLM puro) conforme cenário de negócio.

A seleção de estratégias fica aqui; o pipeline em `rag_pipeline` permanece genérico.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from app.application.services.rag_pipeline import RAGPipelineResult, run_rag_pipeline
from app.application.strategies.generation import OpenAIGenerationStrategy
from app.application.strategies.prompt import (
    DefaultPromptStrategy,
    DirectQuestionPromptStrategy,
    PromptStrategy,
    RestrictiveRagPromptStrategy,
)
from app.application.strategies.retrieval import NoRetrievalStrategy, PgVectorRetrievalStrategy, RetrievalStrategy
from app.infrastructure.db.repositories.experiment_run_repository import ExperimentRunRepository


class RAGScenario(str, Enum):
    """Cenários suportados pela aplicação."""

    LLM = "llm"
    RAG_BASIC = "rag_basic"
    RAG_OPTIMIZED = "rag_optimized"


RAG_BASIC_TOP_K = 3
RAG_OPTIMIZED_DEFAULT_TOP_K = 5
_LLM_PIPELINE_TOP_K = 1
_DEFAULT_CHUNK_SIZE = 300


@dataclass(frozen=True, slots=True)
class ExecuteRAGInput:
    """Entrada do usuário para o caso de uso."""

    question: str
    scenario: RAGScenario
    """Para `rag_optimized`, define quantos documentos recuperar; ignorado nos demais."""
    top_k: int | None = None
    """Reservado para indexação/recorte de texto; ainda não aplicado ao pipeline."""
    chunk_size: int | None = None


def execute_rag(session: Session, data: ExecuteRAGInput) -> RAGPipelineResult:
    """
    Seleciona estratégias conforme `scenario`, executa o pipeline e devolve o resultado.

    - `llm`: sem retrieval; só a pergunta vai ao modelo.
    - `rag_basic`: retrieval com top_k fixo (3) e prompt simples.
    - `rag_optimized`: retrieval com top_k configurável (padrão 5) e prompt restritivo.

    Registra cada execução em `experiment_runs` (latência, tokens, chunks, etc.).
    """
    if not data.question.strip():
        raise ValueError("question não pode ser vazia")

    retrieval, prompt, top_k = _select_strategies(data)
    chunk_size = data.chunk_size if data.chunk_size is not None else _DEFAULT_CHUNK_SIZE

    started = time.perf_counter()
    result = run_rag_pipeline(
        session,
        question=data.question.strip(),
        top_k=top_k,
        retrieval=retrieval,
        prompt=prompt,
        generation=OpenAIGenerationStrategy(),
    )
    latency_s = time.perf_counter() - started

    params: dict[str, Any] = {
        "scenario": data.scenario.value,
        "top_k_requested": data.top_k,
        "top_k_effective": top_k,
        "chunk_size": chunk_size,
    }

    repo = ExperimentRunRepository(session)
    repo.create(
        question=data.question.strip(),
        scenario=data.scenario.value,
        parameters=params,
        top_k=top_k,
        chunk_size=chunk_size,
        retrieved_chunks=result.retrieved_chunks,
        similarity_scores=result.similarity_scores,
        prompt=result.prompt,
        response=result.answer,
        latency_seconds=latency_s,
        tokens_used=result.tokens_used,
    )

    return result


def _select_strategies(
    data: ExecuteRAGInput,
) -> tuple[RetrievalStrategy, PromptStrategy, int]:
    match data.scenario:
        case RAGScenario.LLM:
            return (
                NoRetrievalStrategy(),
                DirectQuestionPromptStrategy(),
                _LLM_PIPELINE_TOP_K,
            )
        case RAGScenario.RAG_BASIC:
            return (
                PgVectorRetrievalStrategy(),
                DefaultPromptStrategy(),
                RAG_BASIC_TOP_K,
            )
        case RAGScenario.RAG_OPTIMIZED:
            k = data.top_k if data.top_k is not None else RAG_OPTIMIZED_DEFAULT_TOP_K
            if k < 1:
                raise ValueError("top_k deve ser >= 1 para o cenário rag_optimized")
            return (
                PgVectorRetrievalStrategy(),
                RestrictiveRagPromptStrategy(),
                k,
            )
