"""Limpeza e divisão de texto para indexação offline."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterator
from pathlib import Path


def clean_text(text: str) -> str:
    """Normaliza Unicode, quebras de linha e espaços em branco."""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Divide o texto em janelas de caracteres com sobreposição (para RAG).

    `overlap` deve ser menor que `chunk_size`; caso contrário é reduzido automaticamente.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size deve ser >= 1")
    if overlap < 0:
        raise ValueError("overlap deve ser >= 0")
    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 5)

    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        start = end - overlap
    return chunks


def iter_txt_files(root: Path, *, recursive: bool = True) -> Iterator[Path]:
    """Lista caminhos `.txt` a partir de `root`."""
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(str(root))
    if recursive:
        yield from sorted(root.rglob("*.txt"))
    else:
        yield from sorted(root.glob("*.txt"))
