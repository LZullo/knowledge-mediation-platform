"""
Execução do benchmark manual via `execute_rag` (sem HTTP).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from pathlib import Path

from sqlalchemy.orm import Session

from app.application.use_cases.execute_rag import (
    RAG_BASIC_TOP_K,
    RAGScenario,
    ExecuteRAGInput,
    execute_rag,
    persist_experiment_run_safe,
)
from app.core.config import get_settings
from app.dados.benchmark_loader import BenchmarkQuestion, load_benchmark_questions
from app.dados.corpus_registry import (
    LEGACY_CORPUS_LABEL,
    effective_retrieval_versions,
    resolve_corpus_version,
)
from app.dados.corpus_stats import get_cumulative_corpus_stats
from app.evaluation.metrics import exact_match_score, f1_score
from app.evaluation.report_models import (
    BenchmarkQuestionResult,
    BenchmarkRunReport,
    BenchmarkScenarioSummary,
    new_run_id,
    utc_now,
)
from app.experiments.exceptions import BenchmarkError, LLMError, PersistenceError, RetrievalError

logger = logging.getLogger(__name__)

DEFAULT_SCENARIOS: tuple[RAGScenario, ...] = (
    RAGScenario.LLM,
    RAGScenario.RAG_BASIC,
    RAGScenario.RAG_OPTIMIZED,
    RAGScenario.RAG_RERANK,
)

PRELIMINARY_SCENARIOS: tuple[RAGScenario, ...] = (
    RAGScenario.LLM,
    RAGScenario.RAG_BASIC,
    RAGScenario.RAG_RERANK,
)

_PRELIMINARY_QUESTIONS_DEFAULT = (
    Path(__file__).resolve().parents[1]
    / "dados"
    / "benchmark_questions_preliminary.json"
)


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _mean_optional_int(values: list[int | None]) -> float | None:
    nums = [v for v in values if v is not None]
    if not nums:
        return None
    return sum(nums) / len(nums)


def _summarize_scenario(
    scenario: str,
    rows: list[BenchmarkQuestionResult],
) -> BenchmarkScenarioSummary:
    rerank_vals = [r.rerank_latency_seconds for r in rows if r.rerank_latency_seconds is not None]
    return BenchmarkScenarioSummary(
        scenario=scenario,
        questions_count=len(rows),
        mean_exact_match=_mean([r.exact_match for r in rows]),
        mean_f1=_mean([r.f1 for r in rows]),
        mean_latency_seconds=_mean([r.latency_seconds for r in rows]),
        mean_retrieval_latency_seconds=_mean(
            [r.retrieval_latency_seconds for r in rows]
        ),
        mean_generation_latency_seconds=_mean(
            [r.generation_latency_seconds for r in rows]
        ),
        mean_tokens_used=_mean_optional_int([r.tokens_used for r in rows]),
        mean_chunks_retrieved=_mean([float(r.chunks_retrieved) for r in rows]),
        mean_prompt_chars=_mean([float(r.prompt_chars) for r in rows]),
        mean_response_chars=_mean([float(r.response_chars) for r in rows]),
        mean_rerank_latency_seconds=_mean(rerank_vals) if rerank_vals else None,
    )


def _log_methodology_notes(
    *,
    corpus_version: str,
    top_k: int | None,
    chunk_size: int,
    scenarios: tuple[RAGScenario, ...],
) -> None:
    logger.info(
        "Benchmark config: corpus_version=%s chunk_size=%s top_k=%s "
        "cenários=%s temperatura=%s",
        corpus_version,
        chunk_size,
        top_k,
        [s.value for s in scenarios],
        get_settings().llm_temperature,
    )


def _run_question(
    session: Session,
    *,
    item: BenchmarkQuestion,
    scenario: RAGScenario,
    top_k: int | None,
    chunk_size: int,
    rerank_top_k: int | None,
    score_threshold: float | None,
    corpus_versions: tuple[str, ...] | None,
    corpus_version: str,
    commit: bool,
    safe_persistence: bool,
) -> BenchmarkQuestionResult:
    settings = get_settings()
    llm_provider = settings.llm_provider.strip().lower()

    inp = ExecuteRAGInput(
        question=item.question,
        scenario=scenario,
        top_k=top_k,
        chunk_size=chunk_size,
        rerank_top_k=rerank_top_k,
        score_threshold=score_threshold,
        corpus_versions=corpus_versions,
    )

    persist = not safe_persistence
    wall_started = time.perf_counter()

    try:
        result = execute_rag(session, inp, persist_experiment=persist)
    except RetrievalError:
        session.rollback()
        logger.exception("Erro de retrieval: cenário=%s", scenario.value)
        raise
    except LLMError:
        session.rollback()
        logger.exception("Erro de LLM: cenário=%s", scenario.value)
        raise

    persistence_error: str | None = None
    persistence_ok = True

    if safe_persistence and not persist:
        from app.application.use_cases.execute_rag import effective_top_k_for_input

        effective_top_k = effective_top_k_for_input(inp)
        err = persist_experiment_run_safe(
            session,
            inp,
            result,
            top_k=effective_top_k,
            chunk_size=chunk_size,
        )
        if err is not None:
            persistence_ok = False
            persistence_error = str(err)
        elif commit:
            session.commit()

    elif commit:
        session.commit()

    latency_seconds = time.perf_counter() - wall_started
    model_answer = result.answer
    em = exact_match_score(model_answer, item.expected_answer)
    f1 = f1_score(model_answer, item.expected_answer)

    row = BenchmarkQuestionResult(
        scenario=scenario.value,
        question=item.question,
        expected_answer=item.expected_answer,
        model_answer=model_answer,
        exact_match=em,
        f1=f1,
        latency_seconds=latency_seconds,
        retrieval_latency_seconds=result.retrieval_latency_seconds,
        generation_latency_seconds=result.generation_latency_seconds,
        total_pipeline_latency_seconds=result.total_latency_seconds,
        tokens_used=result.tokens_used,
        chunks_retrieved=len(result.retrieved_chunks),
        llm_provider=llm_provider,
        model=result.model,
        question_id=item.question_id,
        subset=item.subset,
        corpus_version=corpus_version,
        prompt_chars=result.prompt_chars,
        response_chars=result.response_chars,
        rerank_latency_seconds=result.rerank_latency_seconds,
        persistence_ok=persistence_ok,
        persistence_error=persistence_error,
    )

    logger.info(
        "Scenario=%s | Provider=%s | Model=%s | EM=%.2f | F1=%.2f | "
        "retrieval=%.2fs | generation=%.2fs | total_pipeline=%.2fs | chunks=%s",
        row.scenario,
        row.llm_provider,
        row.model,
        row.exact_match,
        row.f1,
        row.retrieval_latency_seconds,
        row.generation_latency_seconds,
        row.total_pipeline_latency_seconds,
        row.chunks_retrieved,
    )

    print(f"\n--- {scenario.value} | {item.question[:60]}...")
    print(f"Resposta: {model_answer[:500]}")
    print(f"EM={em:.2f} F1={f1:.2f}")

    return row


def run_benchmark(
    session: Session,
    *,
    corpus_version: str = "wikipedia_benchmark_v1",
    limit: int | None = None,
    questions_path: str | None = None,
    scenarios: Sequence[RAGScenario] | None = None,
    top_k: int | None = None,
    rerank_top_k: int | None = None,
    score_threshold: float | None = None,
    chunk_size: int = 300,
    commit_each: bool = True,
    safe_persistence: bool = True,
) -> BenchmarkRunReport:
    """
    Executa todos os cenários sobre perguntas manuais (JSON) e agrega métricas EM/F1.

    Com `safe_persistence=True`, falhas ao gravar `experiment_runs` não interrompem o benchmark.
    """
    scen = tuple(scenarios) if scenarios is not None else DEFAULT_SCENARIOS
    questions = load_benchmark_questions(path=questions_path, limit=limit)
    settings = get_settings()

    if not questions:
        raise BenchmarkError(
            f"nenhuma pergunta carregada (limit={limit}, path={questions_path})"
        )

    version_id = resolve_corpus_version(corpus_version)
    retrieval_versions = effective_retrieval_versions(version_id)
    doc_count, topics_indexed, _mean_len = get_cumulative_corpus_stats(
        session, retrieval_versions
    )

    if doc_count == 0:
        raise BenchmarkError(
            f"corpus vazio para versão {version_id!r} "
            f"(versões de retrieval: {retrieval_versions}). "
            "Execute a indexação antes do benchmark."
        )

    if settings.llm_provider.strip().lower() == "ollama":
        from app.application.providers.ollama_provider import is_ollama_available

        if not is_ollama_available():
            raise BenchmarkError(
                f"Ollama indisponível em {settings.ollama_base_url}. "
                f"Inicie o app/serviço e confirme o modelo (`ollama pull {settings.ollama_model}`) "
                "antes do benchmark — 15 gerações locais podem levar horas."
            )

    _log_methodology_notes(
        corpus_version=version_id,
        top_k=top_k,
        chunk_size=chunk_size,
        scenarios=scen,
    )

    llm_model = (
        settings.ollama_model
        if settings.llm_provider.strip().lower() == "ollama"
        else settings.openai_model
    )

    run_id = new_run_id()
    all_results: list[BenchmarkQuestionResult] = []

    logger.info(
        "Benchmark iniciado: run_id=%s corpus_version=%s docs=%s tópicos=%s "
        "perguntas=%s cenários=%s",
        run_id,
        version_id,
        doc_count,
        len(topics_indexed),
        len(questions),
        [s.value for s in scen],
    )

    for scenario in scen:
        scenario_rows: list[BenchmarkQuestionResult] = []
        logger.info("Cenário %s: %s perguntas", scenario.value, len(questions))

        for idx, item in enumerate(questions, start=1):
            try:
                row = _run_question(
                    session,
                    item=item,
                    scenario=scenario,
                    top_k=top_k,
                    chunk_size=chunk_size,
                    rerank_top_k=rerank_top_k,
                    score_threshold=score_threshold,
                    corpus_versions=retrieval_versions,
                    corpus_version=version_id,
                    commit=commit_each,
                    safe_persistence=safe_persistence,
                )
            except (RetrievalError, LLMError, BenchmarkError):
                raise
            except PersistenceError:
                session.rollback()
                logger.exception(
                    "Erro de persistência (sem safe mode): cenário=%s pergunta=%s/%s",
                    scenario.value,
                    idx,
                    len(questions),
                )
                raise
            except Exception:
                session.rollback()
                logger.exception(
                    "Falha inesperada no benchmark: cenário=%s pergunta=%s/%s",
                    scenario.value,
                    idx,
                    len(questions),
                )
                raise

            scenario_rows.append(row)
            all_results.append(row)

            if idx % 10 == 0 or idx == len(questions):
                logger.info(
                    "Cenário %s: progresso %s/%s model=%s chunks=%s latência=%.2fs "
                    "(EM=%.3f F1=%.3f na última)",
                    scenario.value,
                    idx,
                    len(questions),
                    row.model,
                    row.chunks_retrieved,
                    row.latency_seconds,
                    row.exact_match,
                    row.f1,
                )

        summary = _summarize_scenario(scenario.value, scenario_rows)
        logger.info(
            "Cenário %s concluído: EM=%.4f F1=%.4f latência=%.3fs retrieval=%.3fs "
            "generation=%.3fs tokens=%s chunks=%.2f",
            summary.scenario,
            summary.mean_exact_match,
            summary.mean_f1,
            summary.mean_latency_seconds,
            summary.mean_retrieval_latency_seconds,
            summary.mean_generation_latency_seconds,
            summary.mean_tokens_used,
            summary.mean_chunks_retrieved,
        )

    summaries = [
        _summarize_scenario(s.value, [r for r in all_results if r.scenario == s.value])
        for s in scen
    ]

    legacy_corpus = (
        LEGACY_CORPUS_LABEL
        if version_id == "wikipedia_benchmark_v1"
        else version_id
    )

    return BenchmarkRunReport(
        run_id=run_id,
        created_at=utc_now(),
        corpus=legacy_corpus,
        corpus_version=version_id,
        corpus_document_count=doc_count,
        corpus_chunk_count=doc_count,
        corpus_topics_indexed=list(topics_indexed),
        embedding_model=settings.embedding_model_name,
        rerank_model=settings.rerank_model_name,
        llm_model=llm_model,
        limit=len(questions),
        scenarios=[s.value for s in scen],
        top_k_config=top_k,
        chunk_size_config=chunk_size,
        llm_provider=settings.llm_provider.strip().lower(),
        llm_temperature=settings.llm_temperature,
        summaries=summaries,
        results=all_results,
    )


def run_benchmark_preliminary(
    session: Session,
    *,
    corpus_version: str = "wikipedia_benchmark_v1",
    limit: int = 5,
    questions_path: str | None = None,
    top_k: int | None = 5,
    rerank_top_k: int | None = 10,
    chunk_size: int = 300,
    safe_persistence: bool = True,
    export: bool = True,
    output_dir: Path | str | None = None,
):
    """
    Benchmark preliminar (5 perguntas, cenários llm / rag_basic / rag_rerank).

    Teste 1 histórico: `corpus_version="wikipedia_benchmark_v1"` (alias legado
    `wikipedia_benchmark`). Testes seguintes: `wikipedia_benchmark_v2`, etc.
    """
    from app.evaluation.benchmark_service import run_benchmark_experiment

    path = questions_path or str(_PRELIMINARY_QUESTIONS_DEFAULT)
    return run_benchmark_experiment(
        session,
        corpus_version=corpus_version,
        limit=limit,
        questions_path=path,
        scenarios=PRELIMINARY_SCENARIOS,
        top_k=top_k,
        rerank_top_k=rerank_top_k,
        chunk_size=chunk_size,
        safe_persistence=safe_persistence,
        export=export,
        output_dir=output_dir,
    )
