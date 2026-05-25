"""
Modelos de relatório do benchmark experimental.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class BenchmarkQuestionResult:
    scenario: str
    question: str
    expected_answer: str
    model_answer: str
    exact_match: float
    f1: float
    latency_seconds: float
    tokens_used: int | None
    chunks_retrieved: int
    model: str


@dataclass(frozen=True, slots=True)
class BenchmarkScenarioSummary:
    scenario: str
    questions_count: int
    mean_exact_match: float
    mean_f1: float
    mean_latency_seconds: float
    mean_tokens_used: float | None
    mean_chunks_retrieved: float


@dataclass(frozen=True, slots=True)
class BenchmarkRunReport:
    run_id: str
    created_at: datetime
    corpus: str
    limit: int
    scenarios: list[str]
    summaries: list[BenchmarkScenarioSummary]
    results: list[BenchmarkQuestionResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
