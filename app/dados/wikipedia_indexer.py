"""
Indexação versionada do corpus técnico da Wikipédia em português na tabela `documents`.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.application.services.vector_context import IndexDocumentItem, index_documents
from app.dados.chunking import chunk_wikipedia_page, format_chunk_source
from app.dados.chunking import format_custom_chunk_source
from app.dados.corpus_registry import (
    custom_corpus_for_version,
    get_corpus_definition,
    resolve_corpus_version,
    topics_to_index_for_version,
    wiki_fallbacks_for_version,
)
from app.dados.custom_corpus_loader import load_custom_corpus_documents
from app.dados.wiki_topic_validation import (
    save_validation_report,
    validate_wikipedia_topics,
)
from app.dados.corpus_stats import get_corpus_version_stats
from app.dados.deduplication import (
    load_deduplication_state,
    register_accepted_chunk,
    should_skip_chunk_content,
    should_skip_wikipedia_page,
)
from app.dados.wikipedia_loader import fetch_wikipedia_corpus
from app.infrastructure.db.models.document import Document

logger = logging.getLogger(__name__)

_DEFAULT_EMBED_BATCH_SIZE = 64
_RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"


@dataclass(frozen=True, slots=True)
class WikipediaIndexingReport:
    """Resumo da indexação Wikipédia → `documents`."""

    corpus_version: str
    tier: str
    topics_requested: int
    topics_indexed: tuple[str, ...]
    pages_fetched: int
    topics_skipped: int
    chunks_total: int
    chunks_indexed: int
    chunks_skipped_duplicate_hash: int = 0
    chunks_skipped_similar: int = 0
    chunks_skipped_empty: int = 0
    pages_skipped_already_indexed: int = 0
    mean_chunk_length: float = 0.0
    document_ids: list[int] = field(default_factory=list)
    cleared: bool = False
    chunk_size: int = 500
    chunk_overlap: int = 100
    incremental: bool = True
    report_json_path: str | None = None
    custom_corpus_indexed: tuple[str, ...] = ()
    wiki_validation_path: str | None = None


def _index_items_batched(
    session: Session,
    items: list[IndexDocumentItem],
    *,
    batch_size: int,
) -> list[int]:
    if not items:
        return []
    if batch_size < 1:
        raise ValueError("batch_size deve ser >= 1")
    all_ids: list[int] = []
    total = len(items)
    for start in range(0, total, batch_size):
        batch = items[start : start + batch_size]
        ids = index_documents(session, items=batch)
        all_ids.extend(ids)
        done = min(start + batch_size, total)
        logger.info("Indexação Wikipédia: %s/%s chunks persistidos", done, total)
    return all_ids


def _save_corpus_report(report: WikipediaIndexingReport) -> Path:
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = _RESULTS_DIR / f"corpus_report_{report.corpus_version}.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "corpus_version": report.corpus_version,
        "tier": report.tier,
        "total_documents": report.chunks_indexed,
        "total_chunks": report.chunks_indexed,
        "pages_fetched": report.pages_fetched,
        "topics_requested": report.topics_requested,
        "topics_indexed": list(report.topics_indexed),
        "topics_skipped": report.topics_skipped,
        "duplicates_removed": {
            "hash": report.chunks_skipped_duplicate_hash,
            "similarity": report.chunks_skipped_similar,
            "empty": report.chunks_skipped_empty,
            "page_already_indexed": report.pages_skipped_already_indexed,
        },
        "mean_chunk_length": round(report.mean_chunk_length, 2),
        "chunk_size": report.chunk_size,
        "chunk_overlap": report.chunk_overlap,
        "incremental": report.incremental,
        "cleared": report.cleared,
        "custom_corpus_indexed": list(report.custom_corpus_indexed),
        "wiki_validation_path": report.wiki_validation_path,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Relatório de corpus salvo: %s", path)
    return path


def index_wikipedia_corpus_versioned(
    session: Session,
    corpus_version: str,
    *,
    clear_documents: bool = False,
    incremental: bool | None = None,
    embed_batch_size: int = _DEFAULT_EMBED_BATCH_SIZE,
    commit: bool = True,
    save_report: bool = True,
) -> WikipediaIndexingReport:
    """
    Indexa tópicos conforme definição da versão do corpus, com deduplicação.

    - v1: todos os tópicos iniciais (incremental=False na primeira carga recomendada).
    - v2: apenas tópicos novos (incremental=True por padrão).
    - v3: corpus curado validado + documentação complementar (incremental=False).
    """
    version_id = resolve_corpus_version(corpus_version)
    defn = get_corpus_definition(version_id)
    topic_list = topics_to_index_for_version(version_id)

    if incremental is None:
        incremental = defn.tier == "expanded"

    if clear_documents:
        deleted = session.execute(
            delete(Document).where(Document.corpus_version == version_id)
        ).rowcount
        session.flush()
        logger.warning(
            "Documentos removidos para corpus_version=%s: %s registros",
            version_id,
            deleted,
        )

    logger.info(
        "Iniciando indexação corpus_version=%s tier=%s (%s tópicos, "
        "chunk_size=%s, overlap=%s, incremental=%s)...",
        version_id,
        defn.tier,
        len(topic_list),
        defn.chunk_size,
        defn.chunk_overlap,
        incremental,
    )

    dedup_state = load_deduplication_state(
        session,
        corpus_version=version_id,
        similarity_scope_version=version_id,
    )
    allow_reindex_page = defn.tier == "refined"

    wiki_validation_path: str | None = None
    title_map: dict[str, str] = {}
    if defn.tier == "refined":
        fallbacks = wiki_fallbacks_for_version(version_id)
        candidates = {t: fallbacks.get(t) for t in topic_list}
        validation_entries = validate_wikipedia_topics(candidates)
        wiki_validation_path = str(
            save_validation_report(validation_entries, corpus_version=version_id)
        )
        for entry in validation_entries:
            if entry.indexable and entry.selected_title:
                title_map[entry.topic_requested] = entry.selected_title

    pages, skipped = fetch_wikipedia_corpus(topic_list, title_map=title_map or None)

    index_items: list[IndexDocumentItem] = []
    topics_with_chunks: list[str] = []
    chunk_lengths: list[int] = []

    for page in pages:
        if should_skip_wikipedia_page(
            dedup_state,
            source_topic=page.topic,
            incremental=incremental,
            allow_reindex_page=allow_reindex_page,
        ):
            continue

        chunks = chunk_wikipedia_page(
            page,
            chunk_size=defn.chunk_size,
            overlap=defn.chunk_overlap,
        )
        page_accepted = 0
        for chunk in chunks:
            if should_skip_chunk_content(
                dedup_state,
                content=chunk.content,
                source_topic=page.topic,
            ):
                continue

            digest = register_accepted_chunk(
                dedup_state,
                content=chunk.content,
                source_topic=page.topic,
            )
            source = format_chunk_source(chunk, corpus_version=version_id)
            index_items.append(
                IndexDocumentItem(
                    content=chunk.content,
                    source=source,
                    content_hash=digest,
                    source_url=chunk.source_url,
                    source_topic=chunk.topic,
                    corpus_version=version_id,
                )
            )
            chunk_lengths.append(len(chunk.content))
            page_accepted += 1

        if page_accepted:
            topics_with_chunks.append(page.topic)
            logger.info(
                "Página '%s' (tópico %s): %s chunks aceitos / %s gerados",
                page.title,
                page.topic,
                page_accepted,
                len(chunks),
            )
        else:
            logger.info(
                "Página '%s' (tópico %s): nenhum chunk novo indexado",
                page.title,
                page.topic,
            )

    custom_topics = custom_corpus_for_version(version_id)
    custom_indexed: list[str] = []
    if custom_topics:
        from app.utils.text_processing import chunk_text, clean_text

        for doc in load_custom_corpus_documents(custom_topics):
            cleaned = clean_text(doc.content)
            pieces = chunk_text(
                cleaned,
                chunk_size=defn.chunk_size,
                overlap=defn.chunk_overlap,
            )
            for idx, piece in enumerate(pieces):
                if should_skip_chunk_content(
                    dedup_state,
                    content=piece,
                    source_topic=doc.topic,
                ):
                    continue
                digest = register_accepted_chunk(
                    dedup_state,
                    content=piece,
                    source_topic=doc.topic,
                )
                source = format_custom_chunk_source(
                    topic=doc.topic,
                    title=doc.title,
                    source_url=doc.source_url,
                    chunk_index=idx,
                    corpus_version=version_id,
                )
                index_items.append(
                    IndexDocumentItem(
                        content=piece,
                        source=source,
                        content_hash=digest,
                        source_url=doc.source_url,
                        source_topic=doc.topic,
                        corpus_version=version_id,
                    )
                )
                chunk_lengths.append(len(piece))
            if pieces:
                custom_indexed.append(doc.topic.replace("custom:", ""))
                topics_with_chunks.append(doc.topic)

    document_ids = _index_items_batched(
        session,
        index_items,
        batch_size=embed_batch_size,
    )

    mean_len = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0.0
    counters = dedup_state.counters

    report = WikipediaIndexingReport(
        corpus_version=version_id,
        tier=defn.tier,
        topics_requested=len(topic_list),
        topics_indexed=tuple(topics_with_chunks),
        pages_fetched=len(pages),
        topics_skipped=skipped,
        chunks_total=len(index_items) + counters.skipped_duplicate_hash + counters.skipped_similar_content,
        chunks_indexed=len(index_items),
        chunks_skipped_duplicate_hash=counters.skipped_duplicate_hash,
        chunks_skipped_similar=counters.skipped_similar_content,
        chunks_skipped_empty=counters.skipped_empty_chunk,
        pages_skipped_already_indexed=counters.skipped_duplicate_page,
        mean_chunk_length=mean_len,
        document_ids=document_ids,
        cleared=clear_documents,
        chunk_size=defn.chunk_size,
        chunk_overlap=defn.chunk_overlap,
        incremental=incremental,
        custom_corpus_indexed=tuple(custom_indexed),
        wiki_validation_path=wiki_validation_path,
    )

    report_json_path: str | None = None
    if save_report:
        report_json_path = str(_save_corpus_report(report))

    report = WikipediaIndexingReport(
        corpus_version=report.corpus_version,
        tier=report.tier,
        topics_requested=report.topics_requested,
        topics_indexed=report.topics_indexed,
        pages_fetched=report.pages_fetched,
        topics_skipped=report.topics_skipped,
        chunks_total=report.chunks_total,
        chunks_indexed=report.chunks_indexed,
        chunks_skipped_duplicate_hash=report.chunks_skipped_duplicate_hash,
        chunks_skipped_similar=report.chunks_skipped_similar,
        chunks_skipped_empty=report.chunks_skipped_empty,
        pages_skipped_already_indexed=report.pages_skipped_already_indexed,
        mean_chunk_length=report.mean_chunk_length,
        document_ids=report.document_ids,
        cleared=report.cleared,
        chunk_size=report.chunk_size,
        chunk_overlap=report.chunk_overlap,
        incremental=report.incremental,
        report_json_path=report_json_path,
        custom_corpus_indexed=report.custom_corpus_indexed,
        wiki_validation_path=report.wiki_validation_path,
    )

    stats = get_corpus_version_stats(session, version_id)
    logger.info(
        "Indexação concluída [%s]: %s páginas processadas, %s chunks novos, "
        "%s docs totais na versão, tópicos na versão=%s, média chars/chunk=%.1f",
        version_id,
        report.pages_fetched,
        report.chunks_indexed,
        stats.document_count,
        len(stats.distinct_topics),
        stats.mean_chunk_length,
    )

    if commit:
        session.commit()

    return report


def index_wikipedia_corpus(
    session: Session,
    *,
    topics: tuple[str, ...] | None = None,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    clear_documents: bool = False,
    embed_batch_size: int = _DEFAULT_EMBED_BATCH_SIZE,
    commit: bool = True,
    corpus_version: str = "wikipedia_benchmark_v1",
) -> WikipediaIndexingReport:
    """
    Compatibilidade com API anterior.

    Preferir `index_wikipedia_corpus_versioned` para novos experimentos.
    """
    if topics is not None:
        logger.warning(
            "Parâmetro `topics` customizado em index_wikipedia_corpus; "
            "use index_wikipedia_corpus_versioned para rastreio completo."
        )
    return index_wikipedia_corpus_versioned(
        session,
        corpus_version,
        clear_documents=clear_documents,
        incremental=not clear_documents,
        embed_batch_size=embed_batch_size,
        commit=commit,
    )
