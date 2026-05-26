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
    retrieval_latency_seconds: float
    generation_latency_seconds: float
    total_pipeline_latency_seconds: float
    tokens_used: int | None
    chunks_retrieved: int
    llm_provider: str
    model: str
    persistence_ok: bool = True
    persistence_error: str | None = None


@dataclass(frozen=True, slots=True)
class BenchmarkScenarioSummary:
    scenario: str
    questions_count: int
    mean_exact_match: float
    mean_f1: float
    mean_latency_seconds: float
    mean_retrieval_latency_seconds: float
    mean_generation_latency_seconds: float
    mean_tokens_used: float | None
    mean_chunks_retrieved: float


@dataclass(frozen=True, slots=True)
class BenchmarkRunReport:
    run_id: str
    created_at: datetime
    corpus: str
    corpus_version: str
    corpus_document_count: int
    corpus_chunk_count: int
    corpus_topics_indexed: list[str]
    embedding_model: str
    rerank_model: str
    llm_model: str
    limit: int
    scenarios: list[str]
    top_k_config: int | None
    chunk_size_config: int
    llm_provider: str
    llm_temperature: float
    summaries: list[BenchmarkScenarioSummary]
    results: list[BenchmarkQuestionResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
