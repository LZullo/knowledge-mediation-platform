from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.infrastructure.db.base import Base


def _build_engine():
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=settings.db_echo_sql,
    )


engine = _build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
)


def get_session() -> Generator[Session, None, None]:
    """Gerador de sessão para injeção (ex.: FastAPI Depends)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """Sessão FastAPI: commit ao finalizar com sucesso; rollback em erro."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables() -> None:
    """Cria tabelas a partir dos metadados ORM (desenvolvimento / bootstrap)."""
    import app.infrastructure.db.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
