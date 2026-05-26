"""

Caso de uso: executa o fluxo RAG (ou LLM puro) conforme cenário de negócio.



A seleção de estratégias fica aqui; o pipeline em `rag_pipeline` permanece genérico.

"""



from __future__ import annotations



import logging

from dataclasses import dataclass

from enum import Enum

from typing import Any



from sqlalchemy.orm import Session



from app.application.providers.factory import get_generation_strategy

from app.application.services.rag_pipeline import RAGPipelineResult, run_rag_pipeline

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

from app.core.config import get_settings

from app.experiments.exceptions import LLMError, PersistenceError, RetrievalError

from app.experiments.validation import validate_pipeline_inputs, validate_pipeline_outputs

from app.infrastructure.db.repositories.experiment_run_repository import ExperimentRunRepository



logger = logging.getLogger(__name__)





class RAGScenario(str, Enum):

    """Cenários suportados pela aplicação."""



    LLM = "llm"

    RAG_BASIC = "rag_basic"

    RAG_OPTIMIZED = "rag_optimized"

    RAG_RERANK = "rag_rerank"





RAG_BASIC_TOP_K = 3

RAG_OPTIMIZED_DEFAULT_TOP_K = 5

RAG_RERANK_DEFAULT_TOP_K = 3

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

    """Candidatos iniciais do pgvector no cenário `rag_rerank` (antes do rerank)."""

    rerank_top_k: int | None = None

    """Descarta chunks com score do cross-encoder abaixo deste valor (`rag_rerank`)."""

    score_threshold: float | None = None

    """Versões de `documents.corpus_version` visíveis na recuperação (cumulativo)."""

    corpus_versions: tuple[str, ...] | None = None





def execute_rag(

    session: Session,

    data: ExecuteRAGInput,

    *,

    persist_experiment: bool = True,

) -> RAGPipelineResult:

    """

    Seleciona estratégias conforme `scenario`, executa o pipeline e devolve o resultado.



    - `llm`: sem retrieval; só a pergunta vai ao modelo.

    - `rag_basic`: retrieval com top_k informado (ou padrão) e prompt simples.

    - `rag_optimized`: retrieval com top_k configurável (padrão 5) e prompt restritivo.

    - `rag_rerank`: pgvector expandido + reranking CrossEncoder → top_k final.



    Registra cada execução em `experiment_runs` quando `persist_experiment=True`.

    Falhas de persistência podem ser ignoradas pelo benchmark (`safe_persistence`).

    """

    validate_pipeline_inputs(
        question=data.question,
        scenario=data.scenario.value,
        session=session,
    )



    retrieval, prompt, top_k = _select_strategies(data)

    chunk_size = data.chunk_size if data.chunk_size is not None else _DEFAULT_CHUNK_SIZE

    settings = get_settings()

    generation = get_generation_strategy()

    llm_provider = settings.llm_provider.strip().lower()



    logger.info(

        "RAG iniciado: scenario=%s provider=%s model_cfg=%s top_k=%s",

        data.scenario.value,

        llm_provider,

        settings.ollama_model if llm_provider == "ollama" else settings.openai_model,

        top_k,

    )



    try:

        result = run_rag_pipeline(

            session,

            question=data.question.strip(),

            top_k=top_k,

            retrieval=retrieval,

            prompt=prompt,

            generation=generation,

        )

    except Exception as exc:

        if data.scenario == RAGScenario.LLM:

            raise LLMError(f"falha na geração LLM: {exc!s}") from exc

        raise RetrievalError(f"falha no pipeline RAG: {exc!s}") from exc



    validate_pipeline_outputs(
        scenario=data.scenario.value,
        retrieved_chunks=result.retrieved_chunks,
        prompt=result.prompt,
        answer=result.answer,
    )



    chunks_count = len(result.retrieved_chunks)

    prompt_chars = len(result.prompt)

    response_chars = len(result.answer)



    if result.retrieved_chunks:

        logger.info(

            "Top chunk preview: %s",

            result.retrieved_chunks[0][:200],

        )



    logger.info(

        "RAG concluído: scenario=%s model=%s chunks=%s prompt_chars=%s "

        "response_chars=%s retrieval=%.3fs generation=%.3fs total=%.3fs tokens=%s",

        data.scenario.value,

        result.model,

        chunks_count,

        prompt_chars,

        response_chars,

        result.retrieval_latency_seconds,

        result.generation_latency_seconds,

        result.total_latency_seconds,

        result.tokens_used,

    )



    params = _build_experiment_params(
        data=data,
        result=result,
        top_k=top_k,
        chunk_size=chunk_size,
        llm_provider=llm_provider,
        prompt_chars=prompt_chars,
        response_chars=response_chars,
        chunks_count=chunks_count,
    )

    if persist_experiment:
        _persist_experiment_run(
            session,
            data=data,
            result=result,
            params=params,
            top_k=top_k,
            chunk_size=chunk_size,
            llm_provider=llm_provider,
        )



    return result





def _build_experiment_params(
    *,
    data: ExecuteRAGInput,
    result: RAGPipelineResult,
    top_k: int,
    chunk_size: int,
    llm_provider: str,
    prompt_chars: int,
    response_chars: int,
    chunks_count: int,
) -> dict[str, Any]:
    settings = get_settings()
    return {
        "scenario": data.scenario.value,
        "llm_provider": llm_provider,
        "llm_model": result.model,
        "temperature": settings.llm_temperature,
        "ollama_seed": settings.ollama_seed,
        "top_k_requested": data.top_k,
        "top_k_effective": top_k,
        "chunk_size": chunk_size,
        "rerank_top_k": data.rerank_top_k,
        "score_threshold": data.score_threshold,
        "prompt_chars": prompt_chars,
        "response_chars": response_chars,
        "chunks_retrieved": chunks_count,
        "corpus_versions": list(data.corpus_versions) if data.corpus_versions else None,
        "retrieval_latency_seconds": result.retrieval_latency_seconds,
        "generation_latency_seconds": result.generation_latency_seconds,
        "total_latency_seconds": result.total_latency_seconds,
    }


def _persist_experiment_run(

    session: Session,

    *,

    data: ExecuteRAGInput,

    result: RAGPipelineResult,

    params: dict[str, Any],

    top_k: int,

    chunk_size: int,

    llm_provider: str,

) -> None:

    repo = ExperimentRunRepository(session)

    repo.create(

        question=data.question.strip(),

        scenario=data.scenario.value,

        parameters=params,

        top_k=top_k,

        chunk_size=chunk_size,

        llm_provider=llm_provider,

        llm_model=result.model,

        retrieved_chunks=result.retrieved_chunks,

        similarity_scores=result.similarity_scores,

        prompt=result.prompt,

        response=result.answer,

        retrieval_latency_seconds=result.retrieval_latency_seconds,

        generation_latency_seconds=result.generation_latency_seconds,

        total_latency_seconds=result.total_latency_seconds,

        tokens_used=result.tokens_used,

    )





def persist_experiment_run_safe(

    session: Session,

    data: ExecuteRAGInput,

    result: RAGPipelineResult,

    *,

    top_k: int,

    chunk_size: int,

) -> PersistenceError | None:

    """Tenta persistir após execução; retorna erro sem propagar (modo benchmark seguro)."""

    settings = get_settings()

    llm_provider = settings.llm_provider.strip().lower()

    settings = get_settings()
    chunk_size = data.chunk_size if data.chunk_size is not None else _DEFAULT_CHUNK_SIZE
    prompt_chars = len(result.prompt)
    response_chars = len(result.answer)
    chunks_count = len(result.retrieved_chunks)
    params = _build_experiment_params(
        data=data,
        result=result,
        top_k=top_k,
        chunk_size=chunk_size,
        llm_provider=llm_provider,
        prompt_chars=prompt_chars,
        response_chars=response_chars,
        chunks_count=chunks_count,
    )
    params["safe_persistence_retry"] = True

    try:

        _persist_experiment_run(

            session,

            data=data,

            result=result,

            params=params,

            top_k=top_k,

            chunk_size=chunk_size,

            llm_provider=llm_provider,

        )

        return None

    except PersistenceError as exc:

        session.rollback()

        logger.exception(

            "Persistência falhou (benchmark continua): scenario=%s erro=%s",

            data.scenario.value,

            exc,

        )

        return exc


def effective_top_k_for_input(data: ExecuteRAGInput) -> int:
    _, _, top_k = _select_strategies(data)
    return top_k


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
            k = data.top_k if data.top_k is not None else RAG_BASIC_TOP_K
            if k < 1:
                raise ValueError("top_k deve ser >= 1 para o cenário rag_basic")
            return (
                PgVectorRetrievalStrategy(corpus_versions=data.corpus_versions),
                DefaultPromptStrategy(),
                k,
            )
        case RAGScenario.RAG_OPTIMIZED:
            k = data.top_k if data.top_k is not None else RAG_OPTIMIZED_DEFAULT_TOP_K
            if k < 1:
                raise ValueError("top_k deve ser >= 1 para o cenário rag_optimized")
            return (
                PgVectorRetrievalStrategy(corpus_versions=data.corpus_versions),
                RestrictiveRagPromptStrategy(),
                k,
            )
        case RAGScenario.RAG_RERANK:
            settings = get_settings()
            k = data.top_k if data.top_k is not None else RAG_RERANK_DEFAULT_TOP_K
            if k < 1:
                raise ValueError("top_k deve ser >= 1 para o cenário rag_rerank")
            expanded = (
                data.rerank_top_k
                if data.rerank_top_k is not None
                else settings.rerank_top_k_default
            )
            if expanded < k:
                raise ValueError("rerank_top_k deve ser >= top_k")
            threshold = (
                data.score_threshold
                if data.score_threshold is not None
                else settings.rerank_score_threshold
            )
            return (
                RerankPgVectorRetrievalStrategy(
                    rerank_top_k=expanded,
                    score_threshold=threshold,
                    corpus_versions=data.corpus_versions,
                ),
                RestrictiveRagPromptStrategy(),
                k,
            )

