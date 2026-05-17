from __future__ import annotations

import json
from typing import Any

from app.infrastructure.db.models.experiment_run import ExperimentRun
from app.infrastructure.db.repositories.base import SQLAlchemyRepository


class ExperimentRunRepository(SQLAlchemyRepository):
    """Persistência de execuções de experimento (RAG / LLM)."""

    def create(
        self,
        *,
        question: str,
        scenario: str,
        parameters: dict[str, Any],
        top_k: int,
        chunk_size: int,
        retrieved_chunks: list[str],
        similarity_scores: list[float],
        prompt: str,
        response: str,
        latency_seconds: float,
        tokens_used: int | None,
    ) -> ExperimentRun:
        row = ExperimentRun(
            question=question,
            scenario=scenario,
            top_k=top_k,
            chunk_size=chunk_size,
            parameters=json.dumps(parameters, ensure_ascii=False),
            retrieved_chunks=json.dumps(retrieved_chunks, ensure_ascii=False),
            similarity_scores=json.dumps(similarity_scores),
            prompt=prompt,
            response=response,
            latency=latency_seconds,
            tokens_used=tokens_used if tokens_used is not None else 0,
        )
        self.session.add(row)
        self.session.flush()
        return row
