from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.base import Base


class Language(str, Enum):
    RU = "ru"
    EN = "en"
    DE = "de"
    FR = "fr"


class User(Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[Language | None] = mapped_column(String(2), nullable=True)
    age_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<User {self.tg_id} lang={self.language} 18+={self.age_confirmed}>"