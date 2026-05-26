"""
Indexação versionada do corpus Wikipédia (CLI).

Exemplos:
  python indexar_corpus.py --version wikipedia_benchmark_v1
  python indexar_corpus.py --version wikipedia_benchmark_v2
  python indexar_corpus.py --version wikipedia_benchmark_v3 --no-incremental
"""

from __future__ import annotations

import argparse
import logging

from app.dados.corpus_documentation import write_corpus_versions_doc
from app.dados.corpus_registry import CORPUS_VERSIONS, get_corpus_definition
from app.dados.wikipedia_indexer import index_wikipedia_corpus_versioned
from app.infrastructure.db.connection import SessionLocal, create_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexar corpus Wikipédia versionado")
    parser.add_argument(
        "--version",
        required=True,
        choices=sorted(CORPUS_VERSIONS.keys()),
        help="Identificador da versão do corpus",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Remove apenas documentos desta corpus_version antes de indexar",
    )
    parser.add_argument(
        "--no-incremental",
        action="store_true",
        help="Tenta indexar todos os tópicos da versão (não pula páginas já vistas)",
    )
    args = parser.parse_args()

    defn = get_corpus_definition(args.version)
    incremental = not args.no_incremental and defn.tier == "expanded"

    create_tables(migrate=True)

    with SessionLocal() as session:
        report = index_wikipedia_corpus_versioned(
            session,
            args.version,
            clear_documents=args.clear,
            incremental=incremental,
            commit=True,
        )
        doc_path = write_corpus_versions_doc(session)

    print(report)
    print(f"\nDocumentação: {doc_path}")
    if report.report_json_path:
        print(f"Relatório JSON: {report.report_json_path}")


if __name__ == "__main__":
    main()
