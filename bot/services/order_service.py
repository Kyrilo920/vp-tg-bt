from decimal import Decimal

from sqlalchemy.orm import Session

from bot.db.models.finance import FinanceRecord
from bot.db.models.order import DeliveryType, Order, OrderItem, OrderStatus, PaymentStatus
from bot.domain.cart import Cart
from bot.repositories.finance_repo import FinanceRepository
from bot.repositories.order_repo import OrderRepository
from bot.repositories.product_repo import ProductRepository
from bot.services.commission import CommissionCalculator
from bot.services.delivery import DeliveryCalculator


class OrderService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._orders = OrderRepository(session)
        self._products = ProductRepository(session)
        self._finance = FinanceRepository(session)

    def create_order(
        self,
        cart: Cart,
        tg_user_id: int,
        tg_username: str | None,
        client_name: str,
        phone: str,
        delivery_type: DeliveryType,
        address: str | None = None,
        city: str | None = None,
        zip_code: str | None = None,
        pickup_time: str | None = None,
        comment: str | None = None,
    ) -> Order:
        if cart.is_empty:
            raise ValueError("Cart is empty")

        delivery_price = DeliveryCalculator.calculate(cart.total_quantity, delivery_type)
        items_sum = cart.items_sum
        total_sum = items_sum + delivery_price

        # комиссия — по каждой позиции
        commission_total = Decimal("0")
        for cart_item in cart.items.values():
            commission_total += CommissionCalculator.for_line(
                cart_item.price, cart_item.quantity
            )
        after_commission = items_sum - commission_total

        order = Order(
            tg_user_id=tg_user_id,
            tg_username=tg_username,
            client_name=client_name,
            phone=phone,
            delivery_type=delivery_type,
            address=address,
            city=city,
            zip_code=zip_code,
            pickup_time=pickup_time,
            comment=comment,
            items_sum=items_sum,
            delivery_price=delivery_price,
            total_sum=total_sum,
            order_status=OrderStatus.NEW,
            payment_status=PaymentStatus.PENDING,
        )

        for cart_item in cart.items.values():
            before, after = self._products.decrease_stock(
                cart_item.product_id, cart_item.quantity
            )
            order.items.append(
                OrderItem(
                    product_id=cart_item.product_id,
                    flavor=cart_item.flavor,
                    quantity=cart_item.quantity,
                    price_per_item=cart_item.price,
                    subtotal=cart_item.subtotal,
                    stock_before=before,
                    stock_after=after,
                )
            )

        self._orders.create(order)

        # финансовая запись — со статусом pending, обновится при оплате
        finance = FinanceRecord(
            order_id=order.id,
            items_sum=items_sum,
            delivery_price=delivery_price,
            total_paid=total_sum,
            intermediary_commission=commission_total,
            after_commission=after_commission,
            payment_status=PaymentStatus.PENDING.value,
        )
        self._finance.add(finance)

        self._session.commit()
        return order
