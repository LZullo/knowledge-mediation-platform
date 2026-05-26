"""Estatísticas do corpus indexado por versão."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dados.corpus_registry import CORPUS_VERSIONS, get_corpus_definition
from app.infrastructure.db.models.document import Document


@dataclass(frozen=True, slots=True)
class CorpusVersionStats:
    corpus_version: str
    document_count: int
    distinct_topics: tuple[str, ...]
    mean_chunk_length: float


def count_documents_by_version(session: Session, corpus_version: str) -> int:
    return int(
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.corpus_version == corpus_version)
        )
        or 0
    )


def get_corpus_version_stats(session: Session, corpus_version: str) -> CorpusVersionStats:
    rows = session.execute(
        select(
            Document.source_topic,
            func.length(Document.content),
        ).where(Document.corpus_version == corpus_version)
    ).all()
    topics = sorted({t for t, _ in rows if t})
    lengths = [ln for _, ln in rows if ln]
    mean_len = sum(lengths) / len(lengths) if lengths else 0.0
    return CorpusVersionStats(
        corpus_version=corpus_version,
        document_count=len(rows),
        distinct_topics=tuple(topics),
        mean_chunk_length=mean_len,
    )


def get_cumulative_corpus_stats(
    session: Session,
    corpus_versions: tuple[str, ...],
) -> tuple[int, tuple[str, ...], float]:
    """Contagem cumulativa para retrieval (várias versões)."""
    if not corpus_versions:
        return 0, (), 0.0
    rows = session.execute(
        select(
            Document.source_topic,
            func.length(Document.content),
        ).where(Document.corpus_version.in_(corpus_versions))
    ).all()
    topics = sorted({t for t, _ in rows if t})
    lengths = [ln for _, ln in rows if ln]
    mean_len = sum(lengths) / len(lengths) if lengths else 0.0
    return len(rows), topics, mean_len


def list_indexed_topics(session: Session, corpus_version: str | None = None) -> list[str]:
    stmt = select(Document.source_topic).distinct()
    if corpus_version:
        stmt = stmt.where(Document.corpus_version == corpus_version)
    return sorted(t for t in session.scalars(stmt).all() if t)
