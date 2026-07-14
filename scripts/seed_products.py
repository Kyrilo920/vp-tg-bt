from decimal import Decimal

from bot.db.database import database
from bot.db.models.product import Product

PRODUCTS = [
    ("Watermelon Ice", "Свежий арбузный вкус с холодком", Decimal("20.00"), 12),
    ("Blueberry Raspberry", "Черника и малина", Decimal("20.00"), 10),
    ("Strawberry Watermelon", "Клубника и арбуз", Decimal("20.00"), 10),
    ("Grape Ice", "Виноград с холодком", Decimal("20.00"), 10),
    ("Strawberry Kiwi", "Клубника и киви", Decimal("20.00"), 10),
]

def seed() -> None:
    with database.session() as session:
        for flavor, desc, price, stock in PRODUCTS:
            session.add(
                Product(flavor=flavor, description=desc, price=price, stock=stock)
            )
        session.commit()
    database.dispose()
    print("Товары добавлены")

if __name__ == "__main__":
    seed()
    