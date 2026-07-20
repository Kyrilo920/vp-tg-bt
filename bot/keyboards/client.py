from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.models.product import Product
from bot.db.models.user import Language
from bot.i18n.translations import t


class ClientKeyboards:
    @staticmethod
    def main_menu(lang: Language | None = None) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(t.get("menu_catalog", lang), callback_data="catalog"))
        kb.add(InlineKeyboardButton(t.get("menu_cart", lang), callback_data="cart"))
        kb.add(InlineKeyboardButton(t.get("menu_change_lang", lang), callback_data="change_lang"))
        return kb

    @staticmethod
    def language_choice() -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
            InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang:de"),
            InlineKeyboardButton("🇫🇷 Français", callback_data="lang:fr"),
        )
        return kb

    @staticmethod
    def age_confirm(lang: Language | None = None) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(t.get("age_yes", lang), callback_data="age:yes"))
        kb.add(InlineKeyboardButton(t.get("age_no", lang), callback_data="age:no"))
        return kb

    @staticmethod
    def catalog(products: list[Product], lang: Language | None = None) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        for p in products:
            label = f"{p.flavor} — {p.price} CHF"
            kb.add(InlineKeyboardButton(label, callback_data=f"product:{p.id}"))
        kb.add(InlineKeyboardButton(t.get("menu_cart", lang), callback_data="cart"))
        return kb

    @staticmethod
    def product_card(product_id: int, lang: Language | None = None) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton(t.get("btn_buy", lang), callback_data=f"buy:{product_id}"),
            InlineKeyboardButton(t.get("btn_back", lang), callback_data="catalog"),
        )
        return kb

    @staticmethod
    def quantity_picker(
        product_id: int, max_stock: int, lang: Language | None = None
    ) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup(row_width=4)
        options = [1, 2, 3, 5, 10]
        buttons = [
            InlineKeyboardButton(str(n), callback_data=f"qty:{product_id}:{n}")
            for n in options
            if n <= max_stock
        ]
        kb.add(*buttons)
        kb.add(InlineKeyboardButton(t.get("btn_cancel", lang), callback_data=f"product:{product_id}"))
        return kb

    @staticmethod
    def cart_actions(lang: Language | None = None) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(t.get("btn_add_more", lang), callback_data="catalog"))
        kb.add(InlineKeyboardButton(t.get("btn_clear_cart", lang), callback_data="cart_clear"))
        kb.add(InlineKeyboardButton(t.get("btn_checkout", lang), callback_data="checkout"))
        return kb

    @staticmethod
    def empty_cart(lang: Language | None = None) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(t.get("btn_to_catalog", lang), callback_data="catalog"))
        return kb

    @staticmethod
    def delivery_choice(lang: Language | None = None) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(t.get("btn_delivery", lang), callback_data="dtype:delivery"))
        kb.add(InlineKeyboardButton(t.get("btn_pickup", lang), callback_data="dtype:pickup"))
        kb.add(InlineKeyboardButton(t.get("btn_back_to_cart", lang), callback_data="cart"))
        return kb

    @staticmethod
    def skip_comment(lang: Language | None = None) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(t.get("btn_skip", lang), callback_data="skip_comment"))
        return kb

    @staticmethod
    def confirm_order(lang: Language | None = None) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(t.get("btn_confirm_order", lang), callback_data="order_confirm"))
        kb.add(InlineKeyboardButton(t.get("btn_cancel_order", lang), callback_data="order_cancel"))
        return kb

