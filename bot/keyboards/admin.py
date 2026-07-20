from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.models.order import Order, OrderStatus


class AdminKeyboards:
    @staticmethod
    def panel() -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📋 Новые заказы", callback_data="admin:orders"))
        kb.add(InlineKeyboardButton("📦 Остатки", callback_data="admin:stock"))
        kb.add(InlineKeyboardButton("🍬 Отчёт по вкусам", callback_data="admin:flavors"))
        kb.add(InlineKeyboardButton("🎁 Отчёт по стикерам", callback_data="admin:stickers"))
        kb.add(InlineKeyboardButton("💰 Финансы", callback_data="admin:finance"))
        kb.add(InlineKeyboardButton("✏️ Изменить товар", callback_data="admin:edit_product"))
        return kb

    @staticmethod
    def orders_list(orders: list[Order]) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        for o in orders:
            status = OrderStatus(o.order_status).value
            label = f"#{o.id} • {o.client_name} • {o.total_sum} CHF • {status}"
            kb.add(InlineKeyboardButton(label, callback_data=f"admin:order:{o.id}"))
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="admin:panel"))
        return kb

    @staticmethod
    def order_actions(order_id: int) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔄 Сменить статус", callback_data=f"admin:status:{order_id}"))
        kb.add(InlineKeyboardButton("🕐 Назначить время встречи", callback_data=f"admin:meettime:{order_id}"))
        kb.add(InlineKeyboardButton("⬅️ К списку", callback_data="admin:orders"))
        return kb

    @staticmethod
    def status_choice(order_id: int) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup(row_width=2)
        statuses = [
            (OrderStatus.PAID, "💰 Оплачено"),
            (OrderStatus.ASSEMBLING, "📦 Собирается"),
            (OrderStatus.READY, "✅ Готов к выдаче"),
            (OrderStatus.IN_DELIVERY, "🚚 В доставке"),
            (OrderStatus.COMPLETED, "🎉 Выдан"),
            (OrderStatus.CANCELLED, "❌ Отменён"),
        ]
        for status, label in statuses:
            kb.add(InlineKeyboardButton(label, callback_data=f"admin:setstatus:{order_id}:{status.value}"))
        kb.add(InlineKeyboardButton("⬅️ Отмена", callback_data=f"admin:order:{order_id}"))
        return kb

    @staticmethod
    def products_list(products) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        for p in products:
            kb.add(
                InlineKeyboardButton(
                    f"{p.flavor} • {p.price} CHF • {p.stock} шт",
                    callback_data=f"admin:product:{p.id}",
                )
            )
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="admin:panel"))
        return kb

    @staticmethod
    def product_edit_actions(product_id: int) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("💵 Цена", callback_data=f"admin:pedit:price:{product_id}"),
            InlineKeyboardButton("📦 Остаток", callback_data=f"admin:pedit:stock:{product_id}"),
        )
        kb.add(InlineKeyboardButton("📝 Описание", callback_data=f"admin:pedit:desc:{product_id}"))
        kb.add(InlineKeyboardButton("⬅️ К списку", callback_data="admin:edit_product"))
        return kb
