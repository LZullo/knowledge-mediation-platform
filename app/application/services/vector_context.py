"""Orquestra geração de embeddings e operações no vector store (sem regras de RAG)."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.infrastructure.embeddings import embed_text, embed_texts
from app.infrastructure.vectorstore import PgVectorStore, SimilarDocument


@dataclass(frozen=True, slots=True)
class IndexDocumentItem:
    """Item pronto para indexação com metadados de rastreio."""

    content: str
    source: str
    content_hash: str | None = None
    source_url: str | None = None
    source_topic: str | None = None
    corpus_version: str | None = None


def index_document(
    session: Session,
    *,
    content: str,
    source: str,
    content_hash: str | None = None,
    source_url: str | None = None,
    source_topic: str | None = None,
    corpus_version: str | None = None,
) -> int:
    """Gera embedding, insere em `documents` e devolve o id."""
    embedding = embed_text(content)
    store = PgVectorStore(session)
    row = store.insert_document(
        content=content,
        source=source,
        embedding=embedding,
        content_hash=content_hash,
        source_url=source_url,
        source_topic=source_topic,
        corpus_version=corpus_version,
    )
    return row.id


def index_documents(
    session: Session,
    *,
    items: list[tuple[str, str]] | list[IndexDocumentItem],
) -> list[int]:
    """
    Lote: cada item é (content, source) ou `IndexDocumentItem`.
    Ordem de ids corresponde à ordem dos itens.
    """
    if not items:
        return []

    normalized: list[IndexDocumentItem] = []
    for item in items:
        if isinstance(item, IndexDocumentItem):
            normalized.append(item)
        else:
            content, source = item
            normalized.append(IndexDocumentItem(content=content, source=source))

    contents = [i.content for i in normalized]
    embeddings = embed_texts(contents)
    store = PgVectorStore(session)
    ids: list[int] = []
    for meta, embedding in zip(normalized, embeddings, strict=True):
        row = store.insert_document(
            content=meta.content,
            source=meta.source,
            embedding=embedding,
            content_hash=meta.content_hash,
            source_url=meta.source_url,
            source_topic=meta.source_topic,
            corpus_version=meta.corpus_version,
        )
        ids.append(row.id)
    return ids


def retrieve_similar_documents(
    session: Session,
    *,
    question: str,
    top_k: int,
    corpus_versions: tuple[str, ...] | None = None,
) -> list[SimilarDocument]:
    """Embedding da pergunta + top_k documentos por similaridade (pgvector)."""
    from app.application.strategies.retrieval import PgVectorRetrievalStrategy

    return PgVectorRetrievalStrategy(corpus_versions=corpus_versions).retrieve(
        session, question, top_k
    )
