"""
Coleta de páginas técnicas da Wikipédia em português via MediaWiki API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests

from app.dados.corpus_registry import WIKI_TOPICS_V1 as WIKI_TOPICS

logger = logging.getLogger(__name__)

WIKIPEDIA_API_URL = "https://pt.wikipedia.org/w/api.php"
WIKIPEDIA_BASE_URL = "https://pt.wikipedia.org/wiki/"

_DEFAULT_TIMEOUT = 30.0
_MIN_CONTENT_CHARS = 200
_USER_AGENT = "TCC-RAG-MBA/1.0 (corpus técnico acadêmico; contato local)"


@dataclass(frozen=True, slots=True)
class WikipediaPage:
    """Página obtida da Wikipédia."""

    title: str
    content: str
    source_url: str
    topic: str


def _build_source_url(topic: str) -> str:
    """URL canônica do tópico solicitado (título MediaWiki, como na lista controlada)."""
    return f"{WIKIPEDIA_BASE_URL}{topic}"


def fetch_wikipedia_page(
    topic: str,
    *,
    timeout: float = _DEFAULT_TIMEOUT,
    session: requests.Session | None = None,
) -> WikipediaPage | None:
    """
    Baixa o extract em texto plano de um tópico (título MediaWiki).

    Retorna None se a página não existir, for redirect, tiver extract vazio
    ou estiver abaixo do tamanho mínimo.
    """
    params: dict[str, Any] = {
        "action": "query",
        "prop": "extracts",
        "explaintext": True,
        "titles": topic,
        "format": "json",
    }
    http = session or requests.Session()
    headers = {"User-Agent": _USER_AGENT}

    logger.info("Baixando tópico da Wikipédia: %s", topic)

    try:
        response = http.get(
            WIKIPEDIA_API_URL,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.error("Erro da API Wikipédia para tópico '%s': %s", topic, exc)
        return None
    except ValueError as exc:
        logger.error("Resposta JSON inválida para tópico '%s': %s", topic, exc)
        return None

    pages = data.get("query", {}).get("pages", {})
    if not pages:
        logger.warning("Página ignorada (sem resultado na API): %s", topic)
        return None

    page = next(iter(pages.values()))
    if "missing" in page:
        logger.warning("Página ignorada (título inexistente): %s", topic)
        return None

    if "redirect" in page:
        logger.warning(
            "Página ignorada (redirecionamento): %s → %s",
            topic,
            page.get("title", "?"),
        )
        return None

    title = str(page.get("title", topic))
    extract = page.get("extract") or ""
    if not str(extract).strip():
        logger.warning(
            "Página ignorada (extract vazio): %s (título resolvido: %s)",
            topic,
            title,
        )
        return None

    content = str(extract).strip()
    content_len = len(content)

    if content_len < _MIN_CONTENT_CHARS:
        logger.warning(
            "Página ignorada (conteúdo curto: %s caracteres, mínimo %s): %s",
            content_len,
            _MIN_CONTENT_CHARS,
            topic,
        )
        return None

    source_url = _build_source_url(topic)
    logger.info(
        "Tópico '%s' baixado: título='%s', %s caracteres, url=%s",
        topic,
        title,
        content_len,
        source_url,
    )

    return WikipediaPage(
        title=title,
        content=content,
        source_url=source_url,
        topic=topic,
    )


def fetch_wikipedia_corpus(
    topics: tuple[str, ...] | None = None,
    *,
    timeout: float = _DEFAULT_TIMEOUT,
) -> tuple[list[WikipediaPage], int]:
    """
    Baixa todas as páginas da lista controlada de tópicos.

    Retorna (páginas válidas, quantidade de tópicos ignorados).
    """
    topic_list = topics if topics is not None else WIKI_TOPICS
    pages: list[WikipediaPage] = []
    skipped = 0

    with requests.Session() as http:
        for topic in topic_list:
            page = fetch_wikipedia_page(topic, timeout=timeout, session=http)
            if page is None:
                skipped += 1
                continue
            pages.append(page)

    logger.info(
        "Corpus Wikipédia: %s páginas indexáveis, %s tópicos ignorados (de %s)",
        len(pages),
        skipped,
        len(topic_list),
    )
    return pages, skipped
