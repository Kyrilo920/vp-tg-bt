from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.db.models.product import Product


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all(self) -> list[Product]:
        stmt = select(Product).order_by(Product.id)
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, product_id: int) -> Product | None:
        return self._session.get(Product, product_id)

    def decrease_stock(self, product_id: int, qty: int) -> tuple[int, int]:
        """Возвращает (stock_before, stock_after)."""
        product = self._session.get(Product, product_id, with_for_update=True)
        if product is None:
            raise ValueError(f"Product {product_id} not found")
        if product.stock < qty:
            raise ValueError(f"Not enough stock for {product.flavor}")
        before = product.stock
        product.stock -= qty
        return before, product.stock