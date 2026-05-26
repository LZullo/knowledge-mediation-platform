"""
Deduplicação de chunks para indexação versionada.

- Hash SHA-256 do conteúdo normalizado (dedup exata).
- Bloqueio de reindexação da mesma página Wikipédia (source_topic).
- Similaridade textual > limiar (difflib ou rapidfuzz, se instalado).
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.document import Document
from app.utils.text_processing import clean_text

logger = logging.getLogger(__name__)

DEFAULT_SIMILARITY_THRESHOLD = 0.95

try:
    from rapidfuzz import fuzz

    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False


def normalize_content_for_hash(text: str) -> str:
    """Texto canônico para hash e comparação (NFKC, espaços, minúsculas)."""
    cleaned = clean_text(text)
    return cleaned.casefold()


def content_sha256(text: str) -> str:
    normalized = normalize_content_for_hash(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def text_similarity_ratio(a: str, b: str) -> float:
    na = normalize_content_for_hash(a)
    nb = normalize_content_for_hash(b)
    if not na or not nb:
        return 0.0
    if _HAS_RAPIDFUZZ:
        return fuzz.ratio(na, nb) / 100.0
    return SequenceMatcher(None, na, nb).ratio()


@dataclass
class DeduplicationCounters:
    skipped_duplicate_hash: int = 0
    skipped_duplicate_page: int = 0
    skipped_similar_content: int = 0
    skipped_empty_chunk: int = 0
    details: list[str] = field(default_factory=list)


@dataclass
class CorpusDeduplicationState:
    """Cache em memória durante uma execução de indexação."""

    existing_hashes: set[str]
    existing_contents: list[str]
    indexed_topics: set[str]
    counters: DeduplicationCounters = field(default_factory=DeduplicationCounters)


def load_deduplication_state(
    session: Session,
    *,
    corpus_version: str | None = None,
    similarity_scope_version: str | None = None,
) -> CorpusDeduplicationState:
    """
    Carrega hashes globais e conteúdos para similaridade.

    `similarity_scope_version`: limita comparação textual à versão em indexação
    (evita bloquear chunks refinados v3 por similaridade com v2).
    """
    rows = session.execute(
        select(
            Document.content_hash,
            Document.content,
            Document.source_topic,
            Document.corpus_version,
        )
    ).all()
    hashes: set[str] = set()
    contents: list[str] = []
    topics: set[str] = set()
    sim_version = similarity_scope_version or corpus_version
    for h, content, topic, ver in rows:
        if h:
            hashes.add(h)
        if content and (sim_version is None or ver == sim_version):
            contents.append(content)
        if topic:
            topics.add(topic)
    return CorpusDeduplicationState(
        existing_hashes=hashes,
        existing_contents=contents,
        indexed_topics=topics,
    )


def should_skip_wikipedia_page(
    state: CorpusDeduplicationState,
    *,
    source_topic: str,
    incremental: bool,
    allow_reindex_page: bool = False,
) -> bool:
    if allow_reindex_page or not incremental:
        return False
    if source_topic in state.indexed_topics:
        state.counters.skipped_duplicate_page += 1
        msg = f"Página Wikipédia já indexada (source_topic={source_topic})"
        state.counters.details.append(msg)
        logger.info("Documento ignorado por página já indexada: %s", source_topic)
        return True
    return False


def should_skip_chunk_content(
    state: CorpusDeduplicationState,
    *,
    content: str,
    source_topic: str,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> bool:
    normalized = normalize_content_for_hash(content)
    if not normalized:
        state.counters.skipped_empty_chunk += 1
        logger.info("Chunk ignorado (vazio após normalização): %s", source_topic)
        return True

    digest = content_sha256(content)
    if digest in state.existing_hashes:
        state.counters.skipped_duplicate_hash += 1
        logger.info(
            "Documento ignorado por duplicidade (hash): %s",
            source_topic,
        )
        return True

    for existing in state.existing_contents:
        ratio = text_similarity_ratio(content, existing)
        if ratio > similarity_threshold:
            state.counters.skipped_similar_content += 1
            logger.info(
                "Documento ignorado por similaridade textual (%.2f > %.2f): %s",
                ratio,
                similarity_threshold,
                source_topic,
            )
            state.counters.details.append(
                f"similaridade={ratio:.4f} topic={source_topic}"
            )
            return True

    return False


def register_accepted_chunk(
    state: CorpusDeduplicationState,
    *,
    content: str,
    source_topic: str,
) -> str:
    digest = content_sha256(content)
    state.existing_hashes.add(digest)
    state.existing_contents.append(content)
    state.indexed_topics.add(source_topic)
    return digest
