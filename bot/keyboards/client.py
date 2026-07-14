from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.models.product import Product


class ClientKeyboards:
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🛒 Каталог", callback_data="catalog"))
        kb.add(InlineKeyboardButton("🧺 Корзина", callback_data="cart"))
        return kb

    @staticmethod
    def catalog(products: list[Product]) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        for p in products:
            label = f"{p.flavor} — {p.price} CHF"
            kb.add(InlineKeyboardButton(label, callback_data=f"product:{p.id}"))
        kb.add(InlineKeyboardButton("🧺 Корзина", callback_data="cart"))
        return kb

    @staticmethod
    def product_card(product_id: int) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("🛒 Купить", callback_data=f"buy:{product_id}"),
            InlineKeyboardButton("⬅️ Назад", callback_data="catalog"),
        )
        return kb

    @staticmethod
    def quantity_picker(product_id: int, max_stock: int) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup(row_width=4)
        options = [1, 2, 3, 5, 10]
        buttons = [
            InlineKeyboardButton(str(n), callback_data=f"qty:{product_id}:{n}")
            for n in options
            if n <= max_stock
        ]
        kb.add(*buttons)
        kb.add(InlineKeyboardButton("⬅️ Отмена", callback_data=f"product:{product_id}"))
        return kb

    @staticmethod
    def cart_actions() -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("➕ Добавить ещё товар", callback_data="catalog"))
        kb.add(InlineKeyboardButton("🗑 Очистить корзину", callback_data="cart_clear"))
        kb.add(InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout"))
        return kb

    @staticmethod
    def empty_cart() -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🛒 В каталог", callback_data="catalog"))
        return kb   