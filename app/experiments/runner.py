"""
Execução em lote de experimentos RAG para gerar dados analisáveis (TCC).

Percorre perguntas × cenários × grade (top_k × chunk_size) e chama `execute_rag`,
que persiste cada execução em `experiment_runs`.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from itertools import product

from sqlalchemy.orm import Session

from app.application.use_cases.execute_rag import (
    ExecuteRAGInput,
    RAGScenario,
    execute_rag,
)

logger = logging.getLogger(__name__)

# Grades padrão solicitadas para análise comparativa
DEFAULT_TOP_K_GRID: tuple[int, ...] = (3, 5, 10)
DEFAULT_CHUNK_GRID: tuple[int, ...] = (200, 300, 500)

# Por omissão foca no cenário onde `top_k` afeta a recuperação; inclua outros conforme necessário
DEFAULT_SCENARIOS: tuple[RAGScenario, ...] = (RAGScenario.RAG_OPTIMIZED,)


@dataclass
class BatchRunRecord:
    """Resumo de uma tentativa (sucesso ou falha)."""

    question: str
    scenario: RAGScenario
    top_k: int | None
    chunk_size: int
    ok: bool
    error: str | None = None


@dataclass
class ExperimentBatchReport:
    """Resultado agregado do lote."""

    records: list[BatchRunRecord] = field(default_factory=list)
    total: int = 0
    successes: int = 0
    failures: int = 0


def run_experiment_batch(
    session: Session,
    questions: list[str],
    *,
    scenarios: Sequence[RAGScenario] | None = None,
    top_k_values: Sequence[int] | None = None,
    chunk_size_values: Sequence[int] | None = None,
    commit_each: bool = True,
) -> ExperimentBatchReport:
    """
    Executa automaticamente todas as combinações (pergunta × cenário × top_k × chunk_size).

    Cada chamada bem-sucedida a `execute_rag` grava uma linha em `experiment_runs`.
    Por padrão dá commit após cada execução para não perder dados se o lote falhar no meio.

    Parâmetros `top_k` e `chunk_size` são repassados ao caso de uso (efeito no pipeline conforme cenário).
    """
    cleaned = [q.strip() for q in questions if q and q.strip()]
    if not cleaned:
        raise ValueError("questions deve conter ao menos uma pergunta não vazia")

    scen = tuple(scenarios) if scenarios is not None else DEFAULT_SCENARIOS
    tops = tuple(top_k_values) if top_k_values is not None else DEFAULT_TOP_K_GRID
    chunks = tuple(chunk_size_values) if chunk_size_values is not None else DEFAULT_CHUNK_GRID

    if any(k < 1 for k in tops):
        raise ValueError("todos os valores de top_k devem ser >= 1")
    if any(c < 1 for c in chunks):
        raise ValueError("todos os valores de chunk_size devem ser >= 1")

    report = ExperimentBatchReport()

    for question, scenario, top_k, chunk_size in product(cleaned, scen, tops, chunks):
        report.total += 1
        inp = ExecuteRAGInput(
            question=question,
            scenario=scenario,
            top_k=top_k,
            chunk_size=chunk_size,
        )
        try:
            execute_rag(session, inp)
            if commit_each:
                session.commit()
            report.successes += 1
            report.records.append(
                BatchRunRecord(
                    question=question,
                    scenario=scenario,
                    top_k=top_k,
                    chunk_size=chunk_size,
                    ok=True,
                )
            )
        except Exception as exc:
            session.rollback()
            logger.exception(
                "Falha no experimento: q=%s scenario=%s top_k=%s chunk=%s",
                question[:80],
                scenario.value,
                top_k,
                chunk_size,
            )
            report.failures += 1
            report.records.append(
                BatchRunRecord(
                    question=question,
                    scenario=scenario,
                    top_k=top_k,
                    chunk_size=chunk_size,
                    ok=False,
                    error=str(exc),
                )
            )

    return report
