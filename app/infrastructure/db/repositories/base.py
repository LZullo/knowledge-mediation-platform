from abc import ABC

from sqlalchemy.orm import Session


class SQLAlchemyRepository(ABC):
    """Base para repositórios que usam uma sessão SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        return self._session
