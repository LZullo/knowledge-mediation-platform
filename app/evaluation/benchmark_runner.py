"""
Execução do benchmark manual via `execute_rag` (sem HTTP).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.application.use_cases.execute_rag import (
    RAGScenario,
    ExecuteRAGInput,
    execute_rag,
)
from app.dados.benchmark_loader import BenchmarkQuestion, load_benchmark_questions
from app.evaluation.metrics import exact_match_score, f1_score
from app.evaluation.report_models import (
    BenchmarkQuestionResult,
    BenchmarkRunReport,
    BenchmarkScenarioSummary,
    new_run_id,
    utc_now,
)

logger = logging.getLogger(__name__)

DEFAULT_SCENARIOS: tuple[RAGScenario, ...] = (
    RAGScenario.LLM,
    RAGScenario.RAG_BASIC,
    RAGScenario.RAG_OPTIMIZED,
    RAGScenario.RAG_RERANK,
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
    return BenchmarkScenarioSummary(
        scenario=scenario,
        questions_count=len(rows),
        mean_exact_match=_mean([r.exact_match for r in rows]),
        mean_f1=_mean([r.f1 for r in rows]),
        mean_latency_seconds=_mean([r.latency_seconds for r in rows]),
        mean_tokens_used=_mean_optional_int([r.tokens_used for r in rows]),
        mean_chunks_retrieved=_mean([float(r.chunks_retrieved) for r in rows]),
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
    commit: bool,
) -> BenchmarkQuestionResult:
    inp = ExecuteRAGInput(
        question=item.question,
        scenario=scenario,
        top_k=top_k,
        chunk_size=chunk_size,
        rerank_top_k=rerank_top_k,
        score_threshold=score_threshold,
    )

    started = time.perf_counter()
    result = execute_rag(session, inp)
    latency_seconds = time.perf_counter() - started

    if commit:
        session.commit()

    model_answer = result.answer
    return BenchmarkQuestionResult(
        scenario=scenario.value,
        question=item.question,
        expected_answer=item.expected_answer,
        model_answer=model_answer,
        exact_match=exact_match_score(model_answer, item.expected_answer),
        f1=f1_score(model_answer, item.expected_answer),
        latency_seconds=latency_seconds,
        tokens_used=result.tokens_used,
        chunks_retrieved=len(result.retrieved_chunks),
        model=result.model,
    )


def run_benchmark(
    session: Session,
    *,
    limit: int | None = None,
    questions_path: str | None = None,
    scenarios: Sequence[RAGScenario] | None = None,
    top_k: int | None = None,
    rerank_top_k: int | None = None,
    score_threshold: float | None = None,
    chunk_size: int = 300,
    commit_each: bool = True,
) -> BenchmarkRunReport:
    """
    Executa todos os cenários sobre perguntas manuais (JSON) e agrega métricas EM/F1.
    """
    scen = tuple(scenarios) if scenarios is not None else DEFAULT_SCENARIOS
    questions = load_benchmark_questions(path=questions_path, limit=limit)

    if not questions:
        raise ValueError(
            "nenhuma pergunta carregada do benchmark manual "
            f"(limit={limit}, path={questions_path})"
        )

    run_id = new_run_id()
    all_results: list[BenchmarkQuestionResult] = []

    logger.info(
        "Benchmark iniciado: run_id=%s perguntas=%s cenários=%s",
        run_id,
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
                    commit=commit_each,
                )
            except Exception:
                session.rollback()
                logger.exception(
                    "Falha no benchmark: cenário=%s pergunta=%s/%s",
                    scenario.value,
                    idx,
                    len(questions),
                )
                raise

            scenario_rows.append(row)
            all_results.append(row)

            if idx % 10 == 0 or idx == len(questions):
                logger.info(
                    "Cenário %s: progresso %s/%s (EM=%.3f F1=%.3f na última)",
                    scenario.value,
                    idx,
                    len(questions),
                    row.exact_match,
                    row.f1,
                )

        summary = _summarize_scenario(scenario.value, scenario_rows)
        logger.info(
            "Cenário %s concluído: EM=%.4f F1=%.4f latência=%.3fs tokens=%s chunks=%.2f",
            summary.scenario,
            summary.mean_exact_match,
            summary.mean_f1,
            summary.mean_latency_seconds,
            summary.mean_tokens_used,
            summary.mean_chunks_retrieved,
        )

    summaries = [
        _summarize_scenario(s.value, [r for r in all_results if r.scenario == s.value])
        for s in scen
    ]

    return BenchmarkRunReport(
        run_id=run_id,
        created_at=utc_now(),
        corpus="wikipedia_benchmark",
        limit=len(questions),
        scenarios=[s.value for s in scen],
        summaries=summaries,
        results=all_results,
    )
