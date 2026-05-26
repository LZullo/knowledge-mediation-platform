"""
Chunking de páginas da Wikipédia para indexação RAG.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.dados.wikipedia_loader import WikipediaPage
from app.utils.text_processing import chunk_text, clean_text


@dataclass(frozen=True, slots=True)
class WikiChunk:
    """Fragmento pronto para persistência em `documents`."""

    content: str
    title: str
    topic: str
    source_url: str
    chunk_index: int


def chunk_wikipedia_page(
    page: WikipediaPage,
    *,
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[WikiChunk]:
    """Divide o texto da página em chunks com sobreposição configurável."""
    cleaned = clean_text(page.content)
    pieces = chunk_text(cleaned, chunk_size=chunk_size, overlap=overlap)
    if not pieces:
        return []

    return [
        WikiChunk(
            content=piece,
            title=page.title,
            topic=page.topic,
            source_url=page.source_url,
            chunk_index=idx,
        )
        for idx, piece in enumerate(pieces)
    ]


def format_chunk_source(chunk: WikiChunk, *, corpus_version: str | None = None) -> str:
    """Serializa metadados no campo `source` de `documents`."""
    base = (
        f"wikipedia|topic={chunk.topic}|title={chunk.title}"
        f"|url={chunk.source_url}|chunk={chunk.chunk_index}"
    )
    if corpus_version:
        return f"{base}|corpus_version={corpus_version}"
    return base


def format_custom_chunk_source(
    *,
    topic: str,
    title: str,
    source_url: str,
    chunk_index: int,
    corpus_version: str | None = None,
) -> str:
    """Serializa metadados de corpus complementar curado."""
    base = (
        f"custom_corpus|topic={topic}|title={title}"
        f"|url={source_url}|chunk={chunk_index}"
    )
    if corpus_version:
        return f"{base}|corpus_version={corpus_version}"
    return base


def wiki_chunks_to_index_items(
    chunks: list[WikiChunk],
    *,
    corpus_version: str | None = None,
) -> list[tuple[str, str]]:
    """Converte chunks para pares (content, source) usados por `index_documents`."""
    return [
        (c.content, format_chunk_source(c, corpus_version=corpus_version))
        for c in chunks
    ]


def parse_wikipedia_source(source: str) -> dict[str, str]:
    """Interpreta o campo `source` gerado por `format_chunk_source`."""
    parts = source.split("|")
    result: dict[str, str] = {"kind": parts[0] if parts else ""}
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            result[key] = value
    return result
