from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings

class Database():
    def __init__(self, url: str) -> None:
        self._engine = create_engine(url, echo=False)
        self._session_factory = sessionmaker(
            bind=self._engine, expire_on_commit=False
        )
    
    def session(self) -> Session:
        return self._session_factory()
    
    def dispose(self) -> None:
        return self._engine.dispose()

database = Database(settings.DATABASE_URL)