from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.core.config import get_settings
from app.infrastructure.db.base import Base


class Document(Base):
    """Documento indexável com embedding pgvector e metadados de rastreio experimental."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(get_settings().vector_dimensions),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_topic: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    corpus_version: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
