import telebot
from telebot.storage import StateMemoryStorage
from telebot.custom_filters import StateFilter
from telebot.types import CallbackQuery, Message

from bot.db.database import database
from bot.domain.cart import Cart
from bot.keyboards.client import ClientKeyboards
from bot.repositories.product_repo import ProductRepository
from bot.services.delivery import DeliveryCalculator
from bot.states.cart_states import CartStates
from config import settings

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(token=settings.BOT_TOKEN, state_storage=state_storage)


# ---------- helpers ----------

def load_cart(user_id: int, chat_id: int) -> Cart:
    with bot.retrieve_data(user_id, chat_id) as data:
        return Cart.from_dict(data.get("cart"))


def save_cart(user_id: int, chat_id: int, cart: Cart) -> None:
    with bot.retrieve_data(user_id, chat_id) as data:
        data["cart"] = cart.to_dict()


def render_cart_text(cart: Cart) -> str:
    if cart.is_empty:
        return "🧺 Корзина пуста"

    lines = ["🧺 <b>Ваша корзина:</b>\n"]
    for item in cart.items.values():
        lines.append(
            f"UZY 15K {item.flavor} — {item.quantity} шт × {item.price} = {item.subtotal} CHF"
        )

    delivery = DeliveryCalculator.calculate(cart.total_quantity)
    total = cart.items_sum + delivery
    delivery_str = "бесплатно 🎁" if delivery == 0 else f"{delivery} CHF"

    lines.append(f"\nВсего товаров: <b>{cart.total_quantity}</b> шт")
    lines.append(f"Сумма товаров: <b>{cart.items_sum} CHF</b>")
    lines.append(f"Доставка: <b>{delivery_str}</b>")
    lines.append(f"Итого: <b>{total} CHF</b>")

    if cart.total_quantity >= 5:
        lines.append("\n🎉 Вам доступен бонусный стикерпак!")

    return "\n".join(lines)


# ---------- /start ----------

@bot.message_handler(commands=["start"])
def cmd_start(message: Message) -> None:
    user_name = message.from_user.username or message.from_user.first_name
    text = (
        f"Привет, {user_name}!\n\n"
        f"Я бот-магазин UZY 15K. Открой каталог, чтобы посмотреть вкусы."
    )
    bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=ClientKeyboards.main_menu(),
    )


# ---------- каталог ----------

@bot.callback_query_handler(func=lambda c: c.data == "catalog")
def show_catalog(callback: CallbackQuery) -> None:
    with database.session() as session:
        products = ProductRepository(session).get_all()

    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Выберите вкус:",
        reply_markup=ClientKeyboards.catalog(products),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("product:"))
def show_product(callback: CallbackQuery) -> None:
    product_id = int(callback.data.split(":")[1])

    with database.session() as session:
        product = ProductRepository(session).get_by_id(product_id)

    if product is None:
        bot.answer_callback_query(callback.id, "Товар не найден", show_alert=True)
        return

    stock_line = f"В наличии: {product.stock} шт." if product.stock > 0 else "Нет в наличии"
    text = (
        f"<b>{product.name}</b>\n"
        f"Вкус: {product.flavor}\n\n"
        f"{product.description}\n\n"
        f"Цена: {product.price} CHF\n"
        f"{stock_line}"
    )

    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=ClientKeyboards.product_card(product.id),
    )
    bot.answer_callback_query(callback.id)


# ---------- покупка: выбор количества ----------

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy:"))
def choose_quantity(callback: CallbackQuery) -> None:
    product_id = int(callback.data.split(":")[1])

    with database.session() as session:
        product = ProductRepository(session).get_by_id(product_id)

    if product is None or product.stock == 0:
        bot.answer_callback_query(callback.id, "Нет в наличии", show_alert=True)
        return

    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"Сколько штук <b>{product.flavor}</b> добавить в корзину?",
        parse_mode="HTML",
        reply_markup=ClientKeyboards.quantity_picker(product.id, product.stock),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("qty:"))
def add_to_cart(callback: CallbackQuery) -> None:
    _, product_id_str, qty_str = callback.data.split(":")
    product_id = int(product_id_str)
    qty = int(qty_str)

    with database.session() as session:
        product = ProductRepository(session).get_by_id(product_id)

    if product is None:
        bot.answer_callback_query(callback.id, "Товар не найден", show_alert=True)
        return

    if qty > product.stock:
        bot.answer_callback_query(
            callback.id,
            f"Недостаточно товара. Доступно: {product.stock} шт",
            show_alert=True,
        )
        return

    # достаём корзину, добавляем, сохраняем
    bot.set_state(callback.from_user.id, CartStates.waiting_quantity, callback.message.chat.id)
    cart = load_cart(callback.from_user.id, callback.message.chat.id)
    cart.add(product.id, product.flavor, product.price, qty)
    save_cart(callback.from_user.id, callback.message.chat.id, cart)

    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=render_cart_text(cart),
        parse_mode="HTML",
        reply_markup=ClientKeyboards.cart_actions(),
    )
    bot.answer_callback_query(callback.id, f"Добавлено: {qty} шт")


# ---------- корзина ----------

@bot.callback_query_handler(func=lambda c: c.data == "cart")
def show_cart(callback: CallbackQuery) -> None:
    cart = load_cart(callback.from_user.id, callback.message.chat.id)
    kb = ClientKeyboards.cart_actions() if not cart.is_empty else ClientKeyboards.empty_cart()

    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=render_cart_text(cart),
        parse_mode="HTML",
        reply_markup=kb,
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data == "cart_clear")
def clear_cart(callback: CallbackQuery) -> None:
    cart = Cart()
    save_cart(callback.from_user.id, callback.message.chat.id, cart)
    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="🗑 Корзина очищена",
        reply_markup=ClientKeyboards.empty_cart(),
    )
    bot.answer_callback_query(callback.id, "Корзина очищена")


@bot.callback_query_handler(func=lambda c: c.data == "checkout")
def checkout_stub(callback: CallbackQuery) -> None:
    bot.answer_callback_query(
        callback.id, "Оформление заказа сделаем на следующем шаге 🙂", show_alert=True
    )


# ---------- запуск ----------

if __name__ == "__main__":
    bot.add_custom_filter(StateFilter(bot))
    print("bot was started!")
    bot.infinity_polling()