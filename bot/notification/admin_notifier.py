import logging
from decimal import Decimal

import telebot
from telebot.apihelper import ApiTelegramException

from bot.db.models.order import DeliveryType, Order
from bot.services.commission import CommissionCalculator

logger = logging.getLogger(__name__)


class AdminNotifier:
    def __init__(self, bot: telebot.TeleBot, admin_ids: list[int]) -> None:
        self._bot = bot
        self._admin_ids = admin_ids

    def notify_new_order(self, order: Order) -> None:
        lines = [f"🔔 <b>Новый заказ #{order.id}</b>\n"]
        lines.append(f"Клиент: {order.client_name}")
        if order.tg_username:
            lines.append(f"Telegram: @{order.tg_username}")
        lines.append(f"Телефон: {order.phone}")

        if order.delivery_type == DeliveryType.DELIVERY:
            lines.append("Получение: доставка")
            lines.append(f"Адрес: {order.address}, {order.city}, {order.zip_code}")
        else:
            lines.append("Получение: самовывоз")
            lines.append(f"Время: {order.pickup_time}")

        lines.append("\n<b>Товары:</b>")
        for item in order.items:
            lines.append(
                f"UZY 15K {item.flavor} — {item.quantity} шт × {item.price_per_item} = {item.subtotal} CHF"
            )

        delivery_str = "бесплатно" if order.delivery_price == 0 else f"{order.delivery_price} CHF"
        lines.append(f"\nСумма товаров: {order.items_sum} CHF")
        lines.append(f"Доставка: {delivery_str}")
        lines.append(f"<b>Итого: {order.total_sum} CHF</b>")

        # комиссия
        commission_total = sum(
            (CommissionCalculator.for_line(item.price_per_item, item.quantity) for item in order.items),
            start=Decimal("0"),
        )
        after = order.items_sum - commission_total
        lines.append(f"\nКомиссия посредника: {commission_total} CHF")
        lines.append(f"Сумма после комиссии: {after} CHF")

        lines.append("\n<b>Остатки после заказа:</b>")
        for item in order.items:
            lines.append(f"{item.flavor}: {item.stock_after} шт")

        if order.comment:
            lines.append(f"\nКомментарий: {order.comment}")

        text = "\n".join(lines)
        self._broadcast(text, order.id)

    def notify_paid(self, order: Order) -> None:
        text = (
            f"💰 <b>Заказ #{order.id} оплачен!</b>\n"
            f"Клиент: {order.client_name}\n"
            f"Сумма: {order.total_sum} CHF\n"
            f"Статус: {order.order_status.value}"
        )
        self._broadcast(text, order.id)

    def _broadcast(self, text: str, order_id: int) -> None:
        for admin_id in self._admin_ids:
            try:
                self._bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    parse_mode="HTML",
                )
            except ApiTelegramException:
                logger.exception("Failed to notify admin %s about order #%s", admin_id, order_id)