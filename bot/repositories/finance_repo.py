from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bot.db.models.finance import FinanceRecord


class FinanceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: FinanceRecord) -> FinanceRecord:
        self._session.add(record)
        self._session.flush()
        return record

    def get_by_order(self, order_id: int) -> FinanceRecord | None:
        return self._session.scalar(
            select(FinanceRecord).where(FinanceRecord.order_id == order_id)
        )

    def summary(self) -> dict:
        """Агрегаты по всем оплаченным записям."""
        stmt = select(
            func.count(FinanceRecord.id),
            func.coalesce(func.sum(FinanceRecord.items_sum), 0),
            func.coalesce(func.sum(FinanceRecord.delivery_price), 0),
            func.coalesce(func.sum(FinanceRecord.total_paid), 0),
            func.coalesce(func.sum(FinanceRecord.intermediary_commission), 0),
            func.coalesce(func.sum(FinanceRecord.after_commission), 0),
        ).where(FinanceRecord.payment_status == "paid")

        row = self._session.execute(stmt).one()
        count, items, delivery, total, commission, net = row

        return {
            "orders_count": count,
            "items_sum": Decimal(items),
            "delivery_sum": Decimal(delivery),
            "total_paid": Decimal(total),
            "commission_sum": Decimal(commission),
            "after_commission": Decimal(net),
            "avg_check": Decimal(total) / count if count else Decimal("0"),
        }