"""
Exportação de relatórios de benchmark para JSON e CSV.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from app.evaluation.report_models import BenchmarkRunReport, new_run_id


def _default_output_dir() -> Path:
    # tcc-project/results (irmão de app/)
    app_dir = Path(__file__).resolve().parents[1]
    return app_dir.parent / "results"


def _serialize(obj: object) -> object:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"tipo não serializável: {type(obj)!r}")


def export_benchmark_json(
    report: BenchmarkRunReport,
    *,
    output_dir: Path | str | None = None,
    run_id: str | None = None,
) -> Path:
    """Salva relatório completo em JSON."""
    rid = run_id or report.run_id or new_run_id()
    directory = Path(output_dir) if output_dir is not None else _default_output_dir()
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / f"benchmark_{rid}.json"
    payload = asdict(report)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_serialize),
        encoding="utf-8",
    )
    return path


def export_benchmark_csv(
    report: BenchmarkRunReport,
    *,
    output_dir: Path | str | None = None,
    run_id: str | None = None,
) -> Path:
    """Salva uma linha por pergunta/cenário em CSV tabular."""
    rid = run_id or report.run_id or new_run_id()
    directory = Path(output_dir) if output_dir is not None else _default_output_dir()
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / f"benchmark_{rid}.csv"
    fieldnames = [
        "run_id",
        "corpus_version",
        "embedding_model",
        "rerank_model",
        "llm_model",
        "corpus_document_count",
        "scenario",
        "question",
        "expected_answer",
        "model_answer",
        "exact_match",
        "f1",
        "latency_seconds",
        "retrieval_latency_seconds",
        "generation_latency_seconds",
        "total_pipeline_latency_seconds",
        "tokens_used",
        "chunks_retrieved",
        "llm_provider",
        "model",
        "persistence_ok",
    ]

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in report.results:
            writer.writerow(
                {
                    "run_id": report.run_id,
                    "corpus_version": report.corpus_version,
                    "embedding_model": report.embedding_model,
                    "rerank_model": report.rerank_model,
                    "llm_model": report.llm_model,
                    "corpus_document_count": report.corpus_document_count,
                    "scenario": row.scenario,
                    "question": row.question,
                    "expected_answer": row.expected_answer,
                    "model_answer": row.model_answer,
                    "exact_match": row.exact_match,
                    "f1": row.f1,
                    "latency_seconds": row.latency_seconds,
                    "retrieval_latency_seconds": row.retrieval_latency_seconds,
                    "generation_latency_seconds": row.generation_latency_seconds,
                    "total_pipeline_latency_seconds": row.total_pipeline_latency_seconds,
                    "tokens_used": row.tokens_used if row.tokens_used is not None else "",
                    "chunks_retrieved": row.chunks_retrieved,
                    "llm_provider": row.llm_provider,
                    "model": row.model,
                    "persistence_ok": row.persistence_ok,
                }
            )

    return path


def export_benchmark(
    report: BenchmarkRunReport,
    *,
    output_dir: Path | str | None = None,
) -> tuple[Path, Path]:
    """Exporta JSON completo e CSV tabular com o mesmo run_id."""
    json_path = export_benchmark_json(report, output_dir=output_dir)
    csv_path = export_benchmark_csv(report, output_dir=output_dir, run_id=report.run_id)
    return json_path, csv_path
