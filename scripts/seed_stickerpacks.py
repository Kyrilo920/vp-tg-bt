from bot.db.database import database
from bot.db.models.stickerpack import Stickerpack


STICKERPACKS = [
    ("first_puff", "Первая затяжка", "https://t.me/addstickers/example1"),
    ("our_taste", "Наш вкус", "https://t.me/addstickers/example2"),
    ("forever_yours", "Навсегда твоя", "https://t.me/addstickers/example3"),
]


def seed() -> None:
    with database.session() as session:
        for code, name, link in STICKERPACKS:
            session.add(Stickerpack(code=code, name=name, telegram_link=link))
        session.commit()
    database.dispose()
    print("Стикерпаки добавлены")


if __name__ == "__main__":
    seed()