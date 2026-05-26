"""
Corpus complementar curado (documentos Markdown controlados).

Usado quando a Wikipédia PT não cobre tópicos especializados (ex.: pgvector).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from app.utils.text_processing import clean_text

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CUSTOM_CORPUS_DIR = _PROJECT_ROOT / "docs" / "custom_corpus"


@dataclass(frozen=True, slots=True)
class CustomCorpusDocument:
    """Documento complementar pronto para chunking."""

    topic: str
    title: str
    content: str
    source_url: str
    source_path: str


def load_custom_corpus_documents(
    topic_ids: tuple[str, ...],
    *,
    base_dir: Path | None = None,
) -> list[CustomCorpusDocument]:
    """
    Carrega arquivos `{topic_id}.md` do diretório de corpus complementar.

    Metadados opcionais no topo do arquivo (linhas `key: value` antes do corpo).
    """
    directory = base_dir if base_dir is not None else DEFAULT_CUSTOM_CORPUS_DIR
    documents: list[CustomCorpusDocument] = []

    for topic_id in topic_ids:
        path = directory / f"{topic_id}.md"
        if not path.is_file():
            logger.warning("Documento complementar ausente: %s", path)
            continue
        doc = _parse_markdown_file(path, topic_id=topic_id)
        if doc is None:
            continue
        documents.append(doc)
        logger.info(
            "Corpus complementar carregado: topic=%s chars=%s url=%s",
            topic_id,
            len(doc.content),
            doc.source_url,
        )

    return documents


def _parse_markdown_file(path: Path, *, topic_id: str) -> CustomCorpusDocument | None:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    meta: dict[str, str] = {}
    body_start = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            body_start = idx + 1
            break
        if ":" in stripped and not stripped.startswith("#"):
            key, value = stripped.split(":", 1)
            meta[key.strip().lower()] = value.strip()
            body_start = idx + 1
        else:
            body_start = idx
            break

    body = "\n".join(lines[body_start:]).strip()
    content = clean_text(body)
    if len(content) < 80:
        logger.warning("Documento complementar muito curto: %s", path)
        return None

    title = meta.get("title", topic_id)
    source_url = meta.get("source_url", f"custom_corpus://{topic_id}")

    return CustomCorpusDocument(
        topic=f"custom:{topic_id}",
        title=title,
        content=content,
        source_url=source_url,
        source_path=str(path),
    )
