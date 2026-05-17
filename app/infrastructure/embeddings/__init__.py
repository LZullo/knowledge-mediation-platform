"""Modelos de embedding (geração de vetores; sem acesso a banco)."""

from app.infrastructure.embeddings.embedding_model import embed_text, embed_texts

__all__ = ["embed_text", "embed_texts"]
