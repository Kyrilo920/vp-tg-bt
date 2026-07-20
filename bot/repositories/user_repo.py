from sqlalchemy.orm import Session

from bot.db.models.user import Language, User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_or_create(self, tg_id: int, username: str | None) -> User:
        user = self._session.get(User, tg_id)
        if user is None:
            user = User(tg_id=tg_id, username=username)
            self._session.add(user)
            self._session.flush()
        elif user.username != username:
            user.username = username
        return user

    def set_language(self, tg_id: int, language: Language) -> None:
        user = self._session.get(User, tg_id)
        if user is not None:
            user.language = language

    def confirm_age(self, tg_id: int) -> None:
        user = self._session.get(User, tg_id)
        if user is not None:
            user.age_confirmed = True