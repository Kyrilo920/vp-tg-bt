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