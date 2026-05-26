"""
Validação manual do retrieval (pgvector) sobre o corpus da Wikipédia.
"""

import logging

from app.application.strategies.retrieval.pgvector import PgVectorRetrievalStrategy
from app.dados.chunking import parse_wikipedia_source
from app.infrastructure.db.connection import SessionLocal

logging.basicConfig(level=logging.INFO)

strategy = PgVectorRetrievalStrategy()

QUESTIONS = [
    "O que é machine learning?",
    "O que é PostgreSQL?",
    "O que é uma API REST?",
    "Como funciona Docker?",
    "O que é inteligência artificial?",
]

with SessionLocal() as session:
    for question in QUESTIONS:
        print(f"\n\n######## {question} ########")

        docs = strategy.retrieve(session, question, top_k=5)

        for i, doc in enumerate(docs, start=1):
            meta = parse_wikipedia_source(doc.source)
            print(f"\n--- CHUNK {i} ---")
            print(f"Título: {meta.get('title', '?')}")
            print(f"Tópico: {meta.get('topic', '?')}")
            print(f"URL: {meta.get('url', '?')}")
            print(doc.content[:400])
