"""
Indexação do corpus v1 (reproduzível com o Teste 1).

NÃO usa `clear_documents=True` por padrão — evita apagar versões posteriores.
Use `--clear` apenas para recriar v1 intencionalmente.
"""

import argparse
import logging

from app.dados.corpus_documentation import write_corpus_versions_doc
from app.dados.wikipedia_indexer import index_wikipedia_corpus_versioned
from app.infrastructure.db.connection import SessionLocal, create_tables

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Remove documentos wikipedia_benchmark_v1 antes de reindexar",
    )
    args = parser.parse_args()

    create_tables(migrate=True)

    with SessionLocal() as session:
        report = index_wikipedia_corpus_versioned(
            session,
            "wikipedia_benchmark_v1",
            clear_documents=args.clear,
            incremental=not args.clear,
            commit=True,
        )
        write_corpus_versions_doc(session)

    print(report)
