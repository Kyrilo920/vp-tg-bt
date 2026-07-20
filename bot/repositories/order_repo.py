from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bot.db.models.finance import FinanceRecord
from bot.db.models.order import Order, OrderItem, OrderStatus, PaymentStatus


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, order: Order) -> Order:
        self._session.add(order)
        self._session.flush()
        return order

    def get_by_id(self, order_id: int) -> Order | None:
        return self._session.get(Order, order_id)

    def count_all(self) -> int:
        return self._session.scalar(select(func.count(Order.id))) or 0

    def status_counts(self) -> dict[str, int]:
        """Возвращает количество заказов по каждому статусу."""
        stmt = select(Order.order_status, func.count(Order.id)).group_by(Order.order_status)
        return {status: int(count) for status, count in self._session.execute(stmt).all()}

    def flavor_stats(self) -> list[tuple[str, int]]:
        """Возвращает список (вкус, продано_шт) по оплаченным заказам."""
        stmt = (
            select(OrderItem.flavor, func.sum(OrderItem.quantity))
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.payment_status == PaymentStatus.PAID.value)
            .group_by(OrderItem.flavor)
            .order_by(func.sum(OrderItem.quantity).desc())
        )
        return [(flavor, int(qty)) for flavor, qty in self._session.execute(stmt).all()]

    def list_recent(self, limit: int = 10) -> list[Order]:
        stmt = select(Order).order_by(Order.created_at.desc()).limit(limit)
        return list(self._session.scalars(stmt).all())

    def update_status(self, order_id: int, status: OrderStatus) -> Order | None:
        order = self._session.get(Order, order_id)
        if order is None:
            return None
        order.order_status = status

        if status == OrderStatus.PAID:
            order.payment_status = PaymentStatus.PAID
            finance = self._session.scalar(
                select(FinanceRecord).where(FinanceRecord.order_id == order_id)
            )
            if finance is not None:
                finance.payment_status = PaymentStatus.PAID.value

        return order
