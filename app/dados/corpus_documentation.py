"""
Geração automática de `docs/corpus_versions.md` a partir do registro e do banco.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.dados.corpus_registry import CORPUS_VERSIONS, get_corpus_definition
from app.dados.corpus_stats import get_corpus_version_stats

logger = logging.getLogger(__name__)

_DOCS_PATH = Path(__file__).resolve().parents[2] / "docs" / "corpus_versions.md"


def _format_topics(topics: tuple[str, ...]) -> str:
    if not topics:
        return "_nenhum_"
    return "\n".join(f"- `{t}`" for t in topics)


def generate_corpus_versions_markdown(session: Session) -> str:
    """Monta conteúdo Markdown com estatísticas reais do banco."""
    sections: list[str] = [
        "# Versões do corpus experimental",
        "",
        "Documento gerado/atualizado automaticamente pelo pipeline de indexação. "
        "Preserva rastreabilidade entre benchmarks (Teste 1 = `wikipedia_benchmark_v1`).",
        "",
    ]

    for version_id in sorted(CORPUS_VERSIONS):
        defn = get_corpus_definition(version_id)
        try:
            stats = get_corpus_version_stats(session, version_id)
            doc_count = stats.document_count
            topics_indexed = stats.distinct_topics
            mean_len = stats.mean_chunk_length
        except Exception:
            doc_count = 0
            topics_indexed = ()
            mean_len = 0.0

        sections.append(f"## {version_id}")
        sections.append("")
        sections.append(f"**Tier:** `{defn.tier}`  ")
        if defn.parent_version:
            sections.append(f"**Versão anterior:** `{defn.parent_version}`  ")
        sections.append(
            f"**Chunking:** `chunk_size={defn.chunk_size}`, `overlap={defn.chunk_overlap}`  "
        )
        sections.append("")
        sections.append("### Tópicos solicitados")
        sections.append("")
        sections.append(_format_topics(defn.topics))
        sections.append("")
        if defn.added_topics:
            sections.append("### Tópicos adicionados (em relação à versão anterior)")
            sections.append("")
            sections.append(_format_topics(defn.added_topics))
            sections.append("")
        if defn.custom_corpus_topics:
            sections.append("### Corpus complementar (documentação curada)")
            sections.append("")
            sections.append(
                _format_topics(
                    tuple(f"docs/custom_corpus/{t}.md" for t in defn.custom_corpus_topics)
                )
            )
            sections.append("")
        sections.append("### Estatísticas indexadas (banco)")
        sections.append("")
        sections.append(f"- **Documentos/chunks:** {doc_count}")
        sections.append(f"- **Tópicos com chunks:** {len(topics_indexed)}")
        sections.append(f"- **Tamanho médio do chunk (caracteres):** {mean_len:.1f}")
        sections.append("")
        sections.append("### Motivação")
        sections.append("")
        sections.append(defn.motivation)
        sections.append("")
        sections.append("### Impacto esperado")
        sections.append("")
        sections.append(defn.expected_impact)
        sections.append("")
        sections.append("### Observações de chunking")
        sections.append("")
        sections.append(defn.chunking_notes)
        sections.append("")

    sections.append("---")
    sections.append("")
    sections.append(
        "_Atualize executando `python indexar_corpus.py --version <id>` ou "
        "`python -m app.dados.corpus_documentation` após indexação._"
    )
    return "\n".join(sections)


def write_corpus_versions_doc(session: Session, *, path: Path | None = None) -> Path:
    target = path or _DOCS_PATH
    content = generate_corpus_versions_markdown(session)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    logger.info("Documentação de corpus escrita em %s", target)
    return target
