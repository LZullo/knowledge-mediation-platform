import logging

from app.infrastructure.db.connection import SessionLocal
from app.dados.wikipedia_indexer import index_wikipedia_corpus

logging.basicConfig(level=logging.INFO)

with SessionLocal() as session:
    report = index_wikipedia_corpus(
        session=session,
        clear_documents=True,
        chunk_size=500,
        chunk_overlap=100,
    )

    print(report)
