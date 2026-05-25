"""
Orquestração do benchmark experimental (perguntas manuais → métricas → exportação).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.application.use_cases.execute_rag import RAGScenario
from app.evaluation.benchmark_runner import run_benchmark
from app.evaluation.export import export_benchmark
from app.evaluation.report_models import BenchmarkRunReport

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class BenchmarkExperimentOutput:
    """Resultado da execução + caminhos dos arquivos exportados."""

    report: BenchmarkRunReport
    json_path: Path | None = None
    csv_path: Path | None = None


def run_benchmark_experiment(
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
    output_dir: Path | str | None = None,
    export: bool = True,
) -> BenchmarkExperimentOutput:
    """
    Carrega perguntas do JSON, executa cenários via `execute_rag`, agrega métricas e exporta.

    Parâmetros
    ----------
    top_k:
        Repassado a `rag_optimized` e `rag_rerank` (top_k final no rerank).
    rerank_top_k:
        Candidatos pgvector antes do rerank (`rag_rerank`).
    score_threshold:
        Filtro opcional do cross-encoder (`rag_rerank`).
    output_dir:
        Pasta de saída (padrão: `tcc-project/results/`).
    """
    report = run_benchmark(
        session,
        limit=limit,
        questions_path=questions_path,
        scenarios=scenarios,
        top_k=top_k,
        rerank_top_k=rerank_top_k,
        score_threshold=score_threshold,
        chunk_size=chunk_size,
        commit_each=commit_each,
    )

    json_path: Path | None = None
    csv_path: Path | None = None

    if export:
        json_path, csv_path = export_benchmark(report, output_dir=output_dir)
        logger.info("Benchmark exportado: %s , %s", json_path, csv_path)

    return BenchmarkExperimentOutput(
        report=report,
        json_path=json_path,
        csv_path=csv_path,
    )
