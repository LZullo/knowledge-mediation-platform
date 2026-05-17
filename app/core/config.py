from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# app/.env (independente do diretório de trabalho atual)
_APP_DIR = Path(__file__).resolve().parents[1]
_ENV_FILE = _APP_DIR / ".env"


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente e arquivo `.env`."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "MBA API"
    debug: bool = False

    # PostgreSQL (SQLAlchemy + psycopg v3)
    database_url: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/mba"
    db_echo_sql: bool = False

    # Deve coincidir com a dimensão de saída do modelo de embeddings (ex.: MiniLM = 384).
    vector_dimensions: int = 384
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    # OpenAI — chat completions (ex.: gpt-3.5-turbo, gpt-4o-mini)
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    openai_base_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
