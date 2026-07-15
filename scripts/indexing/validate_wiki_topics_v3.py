"""
Valida títulos Wikipédia PT para o corpus v3 (sem indexar).

Gera: results/wiki_topic_validation_wikipedia_benchmark_v3.json
"""

from __future__ import annotations

import logging

from app.dados.corpus_registry import (
    WIKI_TOPICS_V3_REQUESTED,
    wiki_fallbacks_for_version,
    resolve_corpus_version,
)
from app.dados.wiki_topic_validation import (
    save_validation_report,
    validate_wikipedia_topics,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CORPUS_VERSION = "wikipedia_benchmark_v3"


def main() -> None:
    version_id = resolve_corpus_version(CORPUS_VERSION)
    fallbacks = wiki_fallbacks_for_version(version_id)
    candidates = {t: fallbacks.get(t) for t in WIKI_TOPICS_V3_REQUESTED}
    entries = validate_wikipedia_topics(candidates)
    path = save_validation_report(entries, corpus_version=version_id)
    indexable = sum(1 for e in entries if e.indexable)
    print(f"Validação concluída: {indexable}/{len(entries)} tópicos indexáveis.")
    print(f"Relatório: {path}")


if __name__ == "__main__":
    main()
