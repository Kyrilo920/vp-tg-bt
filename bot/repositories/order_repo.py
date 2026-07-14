from sqlalchemy.orm import Session 

from bot.db.models.order import Order, OrderItem

class OrderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
        
    def create(self, order: Order) -> Order:
        self._session.add(order)
        self._session.flush()
        return order