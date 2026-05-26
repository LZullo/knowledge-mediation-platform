from __future__ import annotations

import json
import logging
from typing import Any

from app.experiments.exceptions import PersistenceError
from app.infrastructure.db.models.experiment_run import ExperimentRun
from app.infrastructure.db.repositories.base import SQLAlchemyRepository

logger = logging.getLogger(__name__)

# Limite explícito para detectar payloads anômalos (PostgreSQL TEXT não trunca).
_MAX_TEXT_FIELD_CHARS = 2_000_000


class ExperimentRunRepository(SQLAlchemyRepository):
    """Persistência de execuções de experimento (RAG / LLM)."""

    @staticmethod
    def _check_field_size(name: str, value: str) -> None:
        size = len(value)
        if size > _MAX_TEXT_FIELD_CHARS:
            raise PersistenceError(
                f"campo {name} excede limite de {_MAX_TEXT_FIELD_CHARS} caracteres "
                f"(tamanho={size})"
            )
        logger.debug("experiment_runs.%s size=%s chars", name, size)

    def create(
        self,
        *,
        question: str,
        scenario: str,
        parameters: dict[str, Any],
        top_k: int,
        chunk_size: int,
        llm_provider: str,
        llm_model: str,
        retrieved_chunks: list[str],
        similarity_scores: list[float],
        prompt: str,
        response: str,
        retrieval_latency_seconds: float,
        generation_latency_seconds: float,
        total_latency_seconds: float,
        tokens_used: int | None,
    ) -> ExperimentRun:
        params_json = json.dumps(parameters, ensure_ascii=False)
        chunks_json = json.dumps(retrieved_chunks, ensure_ascii=False)
        scores_json = json.dumps(similarity_scores)

        for name, payload in (
            ("question", question),
            ("parameters", params_json),
            ("retrieved_chunks", chunks_json),
            ("similarity_scores", scores_json),
            ("prompt", prompt),
            ("response", response),
        ):
            self._check_field_size(name, payload)

        logger.info(
            "Persistindo experiment_run: scenario=%s chunks=%s prompt_chars=%s "
            "response_chars=%s retrieval=%.3fs generation=%.3fs total=%.3fs",
            scenario,
            len(retrieved_chunks),
            len(prompt),
            len(response),
            retrieval_latency_seconds,
            generation_latency_seconds,
            total_latency_seconds,
        )

        row = ExperimentRun(
            question=question,
            scenario=scenario,
            top_k=top_k,
            chunk_size=chunk_size,
            llm_provider=llm_provider,
            llm_model=llm_model,
            parameters=params_json,
            retrieved_chunks=chunks_json,
            similarity_scores=scores_json,
            prompt=prompt,
            response=response,
            retrieval_latency=retrieval_latency_seconds,
            generation_latency=generation_latency_seconds,
            total_latency=total_latency_seconds,
            latency=total_latency_seconds,
            tokens_used=tokens_used if tokens_used is not None else 0,
        )
        try:
            self.session.add(row)
            self.session.flush()
        except Exception as exc:
            raise PersistenceError(
                f"falha ao gravar experiment_run: {exc!s}"
            ) from exc
        return row
