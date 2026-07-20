from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base


class DeliveryType(str, Enum):
    DELIVERY = "delivery"
    PICKUP = "pickup"


class OrderStatus(str, Enum):
    NEW = "new"
    WAITING_PAYMENT = "waiting_payment"
    PAID = "paid"
    ASSEMBLING = "assembling"
    READY = "ready"
    IN_DELIVERY = "in_delivery"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    tg_user_id: Mapped[int] = mapped_column(Integer, index=True)
    tg_username: Mapped[str | None] = mapped_column(String(100), nullable=True)

    client_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(30))
    delivery_type: Mapped[DeliveryType] = mapped_column(String(20))

    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pickup_time: Mapped[str | None] = mapped_column(String(100), nullable=True)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)

    items_sum: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    delivery_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_sum: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order_status: Mapped[OrderStatus] = mapped_column(String(30), default=OrderStatus.NEW)
    payment_status: Mapped[PaymentStatus] = mapped_column(String(30), default=PaymentStatus.PENDING)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Order #{self.id} {self.total_sum} CHF>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    flavor: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer)
    price_per_item: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock_before: Mapped[int] = mapped_column(Integer)
    stock_after: Mapped[int] = mapped_column(Integer)

    order: Mapped[Order] = relationship(back_populates="items")