from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class ExperimentRun(Base):
    """Registro de execução de experimento (parâmetros e resultado)."""

    __tablename__ = "experiment_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    scenario: Mapped[str] = mapped_column(Text, nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False)
    llm_provider: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    parameters: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_chunks: Mapped[str] = mapped_column(Text, nullable=False)
    similarity_scores: Mapped[str] = mapped_column(Text, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    retrieval_latency: Mapped[float | None] = mapped_column(Float, nullable=True)
    generation_latency: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_latency: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency: Mapped[float] = mapped_column(Float, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
