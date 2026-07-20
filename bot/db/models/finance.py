from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.base import Base


class FinanceRecord(Base):
    __tablename__ = "finance_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    items_sum: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    delivery_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    intermediary_commission: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    after_commission: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    payment_status: Mapped[str] = mapped_column(String(30))

    def __repr__(self) -> str:
        return f"<FinanceRecord order#{self.order_id} net={self.after_commission}>"