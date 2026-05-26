"""Validações pré/pós execução do pipeline experimental."""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.experiments.exceptions import ExperimentalValidationError
from app.infrastructure.db.models.document import Document

logger = logging.getLogger(__name__)

_LLM_SCENARIO = "llm"


def assert_corpus_not_empty(session: Session) -> int:
    """Garante que existem documentos indexados antes de cenários RAG."""
    count = session.scalar(select(func.count()).select_from(Document)) or 0
    if count < 1:
        raise ExperimentalValidationError(
            "corpus vazio: nenhum documento na tabela `documents`"
        )
    logger.debug("Corpus validado: %s documentos", count)
    return int(count)


def validate_pipeline_inputs(
    *,
    question: str,
    scenario: str,
    session: Session | None = None,
) -> None:
    if not question.strip():
        raise ExperimentalValidationError("pergunta vazia")
    if scenario != _LLM_SCENARIO and session is not None:
        assert_corpus_not_empty(session)


def validate_pipeline_outputs(
    *,
    scenario: str,
    retrieved_chunks: list[str],
    prompt: str,
    answer: str,
) -> None:
    if not prompt.strip():
        raise ExperimentalValidationError("prompt vazio após montagem")
    if not answer.strip():
        raise ExperimentalValidationError("resposta vazia do modelo")
    if scenario != _LLM_SCENARIO and not retrieved_chunks:
        raise ExperimentalValidationError(
            f"retrieval sem chunks no cenário {scenario}"
        )
