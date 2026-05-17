"""Orquestra geração de embeddings e operações no vector store (sem regras de RAG)."""

from sqlalchemy.orm import Session

from app.application.strategies.retrieval import PgVectorRetrievalStrategy
from app.infrastructure.embeddings import embed_text, embed_texts
from app.infrastructure.vectorstore import PgVectorStore, SimilarDocument


def index_document(session: Session, *, content: str, source: str) -> int:
    """Gera embedding, insere em `documents` e devolve o id."""
    embedding = embed_text(content)
    store = PgVectorStore(session)
    row = store.insert_document(content=content, source=source, embedding=embedding)
    return row.id


def index_documents(
    session: Session,
    *,
    items: list[tuple[str, str]],
) -> list[int]:
    """
    Lote: cada item é (content, source).
    Ordem de ids corresponde à ordem dos itens.
    """
    if not items:
        return []
    contents = [c for c, _ in items]
    embeddings = embed_texts(contents)
    store = PgVectorStore(session)
    ids: list[int] = []
    for (content, source), embedding in zip(items, embeddings, strict=True):
        row = store.insert_document(
            content=content,
            source=source,
            embedding=embedding,
        )
        ids.append(row.id)
    return ids


def retrieve_similar_documents(
    session: Session,
    *,
    question: str,
    top_k: int,
) -> list[SimilarDocument]:
    """Embedding da pergunta + top_k documentos por similaridade (pgvector)."""
    return PgVectorRetrievalStrategy().retrieve(session, question, top_k)
