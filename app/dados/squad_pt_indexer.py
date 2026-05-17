"""
Indexação dos contexts do SQuAD-pt na tabela `documents`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.application.services.vector_context import index_documents
from app.dados.squad_pt_loader import load_squad_pt
from app.infrastructure.db.models.document import Document
from app.utils.text_processing import chunk_text, clean_text

logger = logging.getLogger(__name__)

_DEFAULT_EMBED_BATCH_SIZE = 64


@dataclass(frozen=True, slots=True)
class SquadPTIndexingReport:
    """Resumo da indexação SQuAD-pt → `documents`."""

    split: str
    rows_scanned: int
    unique_contexts: int
    chunks_total: int
    document_ids: list[int] = field(default_factory=list)
    cleared: bool = False


def _dedupe_contexts(contexts: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for ctx in contexts:
        if ctx in seen:
            continue
        seen.add(ctx)
        unique.append(ctx)
    return unique


def _index_items_batched(
    session: Session,
    items: list[tuple[str, str]],
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
        logger.info("Indexação SQuAD-pt: %s/%s chunks persistidos", done, total)
    return all_ids


def index_squad_pt_contexts(
    session: Session,
    limit: int = 1000,
    chunk_size: int = 300,
    chunk_overlap: int = 50,
    clear_documents: bool = False,
    *,
    split: str = "train",
    embed_batch_size: int = _DEFAULT_EMBED_BATCH_SIZE,
    commit: bool = True,
) -> SquadPTIndexingReport:
    """
    Carrega contexts do SQuAD-pt, deduplica, chunka e persiste via `index_documents`.

    `limit` = quantidade máxima de linhas do dataset a ler (antes da deduplicação).
    """
    if limit < 1:
        raise ValueError("limit deve ser >= 1")

    if clear_documents:
        deleted = session.execute(delete(Document)).rowcount
        session.flush()
        logger.info("Tabela documents limpa: %s registros removidos", deleted)

    logger.info("Carregando SQuAD-pt (split=%s, limit=%s)...", split, limit)
    dataset = load_squad_pt(split=split)
    n_rows = min(limit, len(dataset))

    raw_contexts: list[str] = []
    for i in range(n_rows):
        raw_contexts.append(dataset[i]["context"])

    unique_contexts = _dedupe_contexts(raw_contexts)
    logger.info(
        "Contexts: %s linhas lidas → %s contexts únicos",
        n_rows,
        len(unique_contexts),
    )

    items: list[tuple[str, str]] = []
    for ctx_idx, raw_ctx in enumerate(unique_contexts):
        cleaned = clean_text(raw_ctx)
        chunks = chunk_text(cleaned, chunk_size=chunk_size, overlap=chunk_overlap)
        if not chunks:
            continue
        for chunk_idx, chunk in enumerate(chunks):
            source = f"squad-pt/{split}#{ctx_idx}#chunk-{chunk_idx}"
            items.append((chunk, source))

    logger.info("Total de chunks a indexar: %s", len(items))

    document_ids = _index_items_batched(
        session,
        items,
        batch_size=embed_batch_size,
    )

    report = SquadPTIndexingReport(
        split=split,
        rows_scanned=n_rows,
        unique_contexts=len(unique_contexts),
        chunks_total=len(items),
        document_ids=document_ids,
        cleared=clear_documents,
    )

    logger.info(
        "Indexação concluída: %s chunks salvos (%s ids)",
        report.chunks_total,
        len(report.document_ids),
    )

    if commit:
        session.commit()

    return report
