"""Recuperação vetorial direta (pgvector)."""



from __future__ import annotations



from dataclasses import dataclass

from typing import Protocol, runtime_checkable



from sqlalchemy.orm import Session



from app.infrastructure.embeddings import embed_text

from app.infrastructure.vectorstore import PgVectorStore, SimilarDocument





@runtime_checkable

class RetrievalStrategy(Protocol):

    """Define como obter documentos candidatos a partir da pergunta (ex.: top_k)."""



    def retrieve(self, session: Session, question: str, top_k: int) -> list[SimilarDocument]:

        """Retorna documentos ordenados por relevância segundo a estratégia."""

        ...





@dataclass

class PgVectorRetrievalStrategy:

    """Recuperação padrão: embedding da pergunta + similaridade no pgvector."""



    corpus_versions: tuple[str, ...] | None = None



    def retrieve(self, session: Session, question: str, top_k: int) -> list[SimilarDocument]:

        query_embedding = embed_text(question)

        store = PgVectorStore(session)

        return store.search_similar_by_embedding(

            query_embedding,

            top_k=top_k,

            corpus_versions=self.corpus_versions,

        )





class NoRetrievalStrategy:

    """Sem busca na base (cenário apenas LLM). `top_k` é ignorado."""



    def retrieve(self, session: Session, question: str, top_k: int) -> list[SimilarDocument]:

        _ = session, question, top_k

        return []

