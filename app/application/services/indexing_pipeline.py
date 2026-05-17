"""
Indexação offline de arquivos `.txt` para a tabela `documents` (embeddings + pgvector).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

from app.application.services.vector_context import index_documents
from app.utils.text_processing import chunk_text, clean_text, iter_txt_files


@dataclass(frozen=True, slots=True)
class IndexingReport:
    """Resumo de uma corrida de indexação."""

    root: str
    files_indexed: int
    chunks_total: int
    document_ids: list[int]
    errors: list[tuple[str, str]] = field(default_factory=list)


def _index_chunks_batched(
    session: Session,
    items: list[tuple[str, str]],
    *,
    batch_size: int,
) -> list[int]:
    """Chama `index_documents` em lotes para limitar memória na codificação."""
    if not items:
        return []
    if batch_size < 1:
        raise ValueError("batch_size deve ser >= 1")
    all_ids: list[int] = []
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        all_ids.extend(index_documents(session, items=batch))
    return all_ids


def index_txt_directory(
    session: Session,
    *,
    directory: Path | str,
    chunk_size: int = 300,
    chunk_overlap: int = 50,
    recursive: bool = True,
    encoding: str = "utf-8",
    embed_batch_size: int = 64,
    commit: bool = True,
) -> IndexingReport:
    """
    Lê `.txt`, limpa, divide em chunks, gera embeddings e persiste em `documents`.

    Cada chunk é armazenado com `source` no formato `{caminho/relativo}#chunk-{índice}`.

    Se `commit` for True (padrão), faz `session.commit()` ao final (uso típico em script offline).
    """
    root = Path(directory).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"não é diretório: {root}")

    document_ids: list[int] = []
    errors: list[tuple[str, str]] = []
    files_done = 0
    chunks_count = 0

    for path in iter_txt_files(root, recursive=recursive):
        try:
            raw = path.read_text(encoding=encoding, errors="replace")
            cleaned = clean_text(raw)
            chunks = chunk_text(cleaned, chunk_size=chunk_size, overlap=chunk_overlap)
            if not chunks:
                continue
            rel = path.relative_to(root).as_posix()
            items: list[tuple[str, str]] = [
                (chunk, f"{rel}#chunk-{i}") for i, chunk in enumerate(chunks)
            ]
            ids = _index_chunks_batched(
                session,
                items,
                batch_size=embed_batch_size,
            )
            document_ids.extend(ids)
            chunks_count += len(chunks)
            files_done += 1
        except Exception as exc:
            errors.append((str(path), str(exc)))

    report = IndexingReport(
        root=str(root),
        files_indexed=files_done,
        chunks_total=chunks_count,
        document_ids=document_ids,
        errors=errors,
    )
    if commit:
        session.commit()
    return report
