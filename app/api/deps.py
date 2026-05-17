"""Dependências compartilhadas das rotas."""

from app.infrastructure.db import get_db

__all__ = ["get_db"]
