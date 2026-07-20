from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.db.models.stickerpack import Stickerpack


class StickerpackRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all(self) -> list[Stickerpack]:
        return list(self._session.scalars(select(Stickerpack).order_by(Stickerpack.id)).all())

    def get_by_code(self, code: str) -> Stickerpack | None:
        return self._session.scalar(select(Stickerpack).where(Stickerpack.code == code))

    def increment_selected(self, code: str) -> None:
        pack = self.get_by_code(code)
        if pack is not None:
            pack.selected_count += 1

    def stats(self) -> list[tuple[str, int]]:
        """Возвращает список (name, selected_count) от популярных к менее популярным."""
        stmt = select(Stickerpack).order_by(Stickerpack.selected_count.desc())
        return [(p.name, p.selected_count) for p in self._session.scalars(stmt).all()]