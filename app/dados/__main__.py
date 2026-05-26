"""CLI: regenerar docs/corpus_versions.md a partir do banco."""

import logging

from app.dados.corpus_documentation import write_corpus_versions_doc
from app.infrastructure.db.connection import SessionLocal, create_tables

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    create_tables(migrate=True)
    with SessionLocal() as session:
        path = write_corpus_versions_doc(session)
    print(path)
