"""
Validação prévia de títulos MediaWiki (Wikipédia PT) antes da indexação.

Gera relatório com existência, redirecionamentos e título selecionável para indexação.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from app.dados.wikipedia_loader import (
    WIKIPEDIA_API_URL,
    WIKIPEDIA_BASE_URL,
    _DEFAULT_TIMEOUT,
    _MIN_CONTENT_CHARS,
    _USER_AGENT,
)

logger = logging.getLogger(__name__)

_RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"


@dataclass(frozen=True, slots=True)
class WikiTopicValidationEntry:
    topic_requested: str
    topic_exists: bool
    redirect_exists: bool
    resolved_title: str | None
    fallback_title: str | None
    fallback_exists: bool
    selected_title: str | None
    extract_chars: int
    indexable: bool
    status: str
    notes: str = ""


def _query_pages(
    titles: list[str],
    *,
    timeout: float = _DEFAULT_TIMEOUT,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "action": "query",
        "prop": "extracts",
        "explaintext": True,
        "redirects": 1,
        "titles": "|".join(titles),
        "format": "json",
    }
    http = session or requests.Session()
    response = http.get(
        WIKIPEDIA_API_URL,
        params=params,
        headers={"User-Agent": _USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def _resolve_content_page(
    data: dict[str, Any],
    topic_requested: str,
) -> tuple[dict[str, Any], bool, str | None]:
    """Retorna página com extract, se houve redirect e título resolvido."""
    query = data.get("query", {})
    redirects = query.get("redirects", [])
    redirect_to: str | None = None
    for item in redirects:
        if str(item.get("from", "")) == topic_requested:
            redirect_to = str(item.get("to", ""))
            break

    pages_raw = query.get("pages", {})
    if not pages_raw:
        return {"missing": True}, bool(redirect_to), redirect_to

    # Com redirects=1, o extract costuma vir na página de destino.
    page = next(iter(pages_raw.values()))
    resolved = str(page.get("title", redirect_to or topic_requested))
    return page, bool(redirect_to), redirect_to or resolved


def _page_status(
    page: dict[str, Any],
    *,
    topic_requested: str,
    redirect_exists: bool,
    resolved_title: str | None,
    fallback_title: str | None,
    fallback_page: dict[str, Any] | None,
    fallback_redirect: bool,
) -> WikiTopicValidationEntry:
    missing = "missing" in page
    title = str(page.get("title", resolved_title or topic_requested)) if not missing else None
    extract = (page.get("extract") or "").strip()
    extract_len = len(extract)

    fb_missing = fallback_page is None or "missing" in fallback_page
    fb_title = (
        str(fallback_page.get("title", fallback_title))
        if fallback_page and not fb_missing
        else None
    )
    fb_extract_len = (
        len((fallback_page.get("extract") or "").strip()) if fallback_page and not fb_missing else 0
    )

    selected: str | None = None
    status = "missing"
    notes = ""

    if not missing and extract_len >= _MIN_CONTENT_CHARS:
        selected = title
        status = "ok_redirect" if redirect_exists else "ok"
        if redirect_exists:
            notes = f"Título redireciona; indexar como '{title}'."
    elif not missing and extract_len < _MIN_CONTENT_CHARS:
        status = "short_extract"
        notes = f"Extract com {extract_len} caracteres (mínimo {_MIN_CONTENT_CHARS})."
    elif missing:
        status = "missing"
        notes = "Título inexistente na Wikipédia PT."

    if selected is None and not fb_missing and fb_extract_len >= _MIN_CONTENT_CHARS:
        selected = fb_title
        status = "ok_fallback"
        notes = f"Fallback '{fallback_title}' utilizável."
        if fallback_redirect:
            notes += " (fallback via redirect)."
    elif selected is None and not fb_missing and 0 < fb_extract_len < _MIN_CONTENT_CHARS:
        status = "short_extract_fallback"
        notes = f"Fallback com extract curto ({fb_extract_len} chars)."

    indexable = selected is not None

    return WikiTopicValidationEntry(
        topic_requested=topic_requested,
        topic_exists=not missing or redirect_exists,
        redirect_exists=redirect_exists,
        resolved_title=resolved_title or title,
        fallback_title=fallback_title,
        fallback_exists=not fb_missing,
        selected_title=selected,
        extract_chars=extract_len if not missing else 0,
        indexable=indexable,
        status=status,
        notes=notes,
    )


def validate_wikipedia_topic(
    topic: str,
    *,
    fallback_title: str | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
    session: requests.Session | None = None,
) -> WikiTopicValidationEntry:
    """Valida um título (e fallback opcional) contra a API MediaWiki."""
    data = _query_pages([topic], timeout=timeout, session=session)
    primary, redirect_exists, resolved = _resolve_content_page(data, topic)

    fallback_page = None
    fb_redirect = False
    if fallback_title and fallback_title != topic:
        fb_data = _query_pages([fallback_title], timeout=timeout, session=session)
        fallback_page, fb_redirect, _ = _resolve_content_page(fb_data, fallback_title)

    return _page_status(
        primary,
        topic_requested=topic,
        redirect_exists=redirect_exists,
        resolved_title=resolved,
        fallback_title=fallback_title,
        fallback_page=fallback_page,
        fallback_redirect=fb_redirect,
    )


def validate_wikipedia_topics(
    topics: dict[str, str | None],
    *,
    timeout: float = _DEFAULT_TIMEOUT,
) -> list[WikiTopicValidationEntry]:
    """
    Valida vários tópicos.

    `topics`: mapa título solicitado → fallback opcional.
    """
    entries: list[WikiTopicValidationEntry] = []
    with requests.Session() as http:
        for topic, fallback in topics.items():
            try:
                entry = validate_wikipedia_topic(
                    topic,
                    fallback_title=fallback,
                    timeout=timeout,
                    session=http,
                )
            except requests.RequestException as exc:
                entry = WikiTopicValidationEntry(
                    topic_requested=topic,
                    topic_exists=False,
                    redirect_exists=False,
                    resolved_title=None,
                    fallback_title=fallback,
                    fallback_exists=False,
                    selected_title=None,
                    extract_chars=0,
                    indexable=False,
                    status="api_error",
                    notes=str(exc),
                )
            entries.append(entry)
            logger.info(
                "Validação wiki: %s → status=%s indexable=%s selected=%s",
                topic,
                entry.status,
                entry.indexable,
                entry.selected_title,
            )
    return entries


def save_validation_report(
    entries: list[WikiTopicValidationEntry],
    *,
    corpus_version: str,
    output_path: Path | str | None = None,
) -> Path:
    path = (
        Path(output_path)
        if output_path is not None
        else _RESULTS_DIR / f"wiki_topic_validation_{corpus_version}.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    indexable = [e.selected_title for e in entries if e.indexable and e.selected_title]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "corpus_version": corpus_version,
        "topics_validated": len(entries),
        "topics_indexable": len(indexable),
        "indexable_titles": indexable,
        "entries": [asdict(e) for e in entries],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Relatório de validação salvo: %s", path)
    return path


def build_source_url(topic: str) -> str:
    return f"{WIKIPEDIA_BASE_URL}{topic}"
