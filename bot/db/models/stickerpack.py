from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.base import Base

class Stickerpack(Base):
    __tablename__ = "stickerpacks"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    telegram_link: Mapped[str] = mapped_column(String(200))
    selected_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<Stickerpack {self.name}>"