from app.infrastructure.db.connection import SessionLocal

from app.application.strategies.retrieval.pgvector import PgVectorRetrievalStrategy

from app.dados.chunking import parse_wikipedia_source



strategy = PgVectorRetrievalStrategy()



questions = [

    "O que é machine learning?",

    "O que é uma API REST?",

    "O que é inteligência artificial?",

    "O que é PostgreSQL?",

]



with SessionLocal() as session:

    for question in questions:

        print(f"\n\n######## {question} ########")



        docs = strategy.retrieve(

            session,

            question,

            top_k=5,

        )



        for i, doc in enumerate(docs, start=1):

            meta = parse_wikipedia_source(doc.source)

            print(f"\n--- DOCUMENTO {i} ---")

            print(f"Título: {meta.get('title', '?')} | URL: {meta.get('url', '?')}")

            print(doc.content[:400])

