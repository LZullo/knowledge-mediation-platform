from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env na raiz do projeto ou em app/ (independente do cwd)
_APP_DIR = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = _APP_DIR.parent
_ENV_CANDIDATES = (_PROJECT_ROOT / ".env", _APP_DIR / ".env")
_ENV_FILES = [str(p) for p in _ENV_CANDIDATES if p.is_file()]


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente e arquivo `.env`."""

    model_config = SettingsConfigDict(
        env_file=tuple(_ENV_FILES) if _ENV_FILES else str(_APP_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "MBA API"
    debug: bool = False

    # PostgreSQL (SQLAlchemy + psycopg v3)
    database_url: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5433/mba"
    db_echo_sql: bool = False

    # Deve coincidir com a dimensão de saída do modelo de embeddings (ex.: MiniLM = 384).
    vector_dimensions: int = 384
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Reranking (CrossEncoder local; sem OpenAI)
    rerank_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_top_k_default: int = 10
    rerank_score_threshold: float | None = None

    # OpenAI — chat completions (ex.: gpt-3.5-turbo, gpt-4o-mini)
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    openai_base_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
