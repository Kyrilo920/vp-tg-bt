import telebot
from telebot.apihelper import ApiTelegramException
from telebot.storage import StateMemoryStorage
from telebot.custom_filters import StateFilter
from telebot.types import CallbackQuery, Message

from bot.db.database import database
from bot.db.models.order import DeliveryType, OrderStatus, PaymentStatus
from bot.db.models.user import Language, User
from bot.i18n.translations import t
from bot.repositories.user_repo import UserRepository
from bot.domain.cart import Cart
from bot.filters.admin_filter import IsAdminFilter
from bot.keyboards.admin import AdminKeyboards
from bot.keyboards.client import ClientKeyboards
from bot.notification.admin_notifier import AdminNotifier
from bot.repositories.finance_repo import FinanceRepository
from bot.repositories.order_repo import OrderRepository
from bot.repositories.product_repo import ProductRepository
from bot.services.delivery import DeliveryCalculator
from bot.services.order_service import OrderService
from bot.states.cart_states import AdminStates, CartStates, CheckoutStates
from config import settings


ADMIN_IDS = [
    aid for aid in (settings.ADMIN_ID, settings.ADMIN_ID_2, settings.ADMIN_ID_3) if aid is not None
]

PICKUP_ADDRESS_LINK = "https://maps.app.goo.gl/aSMmisUE7nFm83uy6?g_st=ic"

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(token=settings.BOT_TOKEN, state_storage=state_storage)
notifier = AdminNotifier(bot, ADMIN_IDS)


# ---------- helpers ----------

def safe_edit_message(**kwargs) -> None:
    """edit_message_text, но не падает, если новый текст совпадает с текущим (Telegram 400),
    и переживает переход с фото-сообщения на текстовое (пересоздаёт сообщение)."""
    try:
        bot.edit_message_text(**kwargs)
    except ApiTelegramException as e:
        if "message is not modified" in str(e):
            return
        if "there is no text in the message to edit" in str(e):
            chat_id = kwargs["chat_id"]
            message_id = kwargs["message_id"]
            try:
                bot.delete_message(chat_id, message_id)
            except Exception:
                pass
            bot.send_message(
                chat_id,
                kwargs["text"],
                parse_mode=kwargs.get("parse_mode"),
                reply_markup=kwargs.get("reply_markup"),
            )
            return
        raise


def load_cart(user_id: int, chat_id: int) -> Cart:
    with bot.retrieve_data(user_id, chat_id) as data:
        return Cart.from_dict(data.get("cart"))


def save_cart(user_id: int, chat_id: int, cart: Cart) -> None:
    with bot.retrieve_data(user_id, chat_id) as data:
        data["cart"] = cart.to_dict()


def render_cart_text(cart: Cart, lang: Language | None = None) -> str:
    if cart.is_empty:
        return t.get("cart_empty", lang)

    lines = [t.get("your_cart", lang), ""]
    for item in cart.items.values():
        lines.append(
            f"UZY 15K {item.flavor} — {item.quantity} × {item.price} = {item.subtotal} CHF"
        )

    delivery = DeliveryCalculator.calculate(cart.total_quantity)
    total = cart.items_sum + delivery
    delivery_str = t.get("delivery_free", lang) if delivery == 0 else f"{delivery} CHF"

    lines.append(f"\n{t.get('total_items', lang)}: <b>{cart.total_quantity}</b>")
    lines.append(f"{t.get('items_sum', lang)}: <b>{cart.items_sum} CHF</b>")
    lines.append(f"{t.get('delivery', lang)}: <b>{delivery_str}</b>")
    lines.append(f"{t.get('total', lang)}: <b>{total} CHF</b>")

    return "\n".join(lines)


def get_user(tg_id: int, username: str | None) -> User:
    """Возвращает пользователя из БД, создаёт при первом запуске."""
    with database.session() as session:
        user = UserRepository(session).get_or_create(tg_id, username)
        session.commit()
        # detached-объект: обновляем поля вручную, они уже загружены
        session.expunge(user)
        return user


def ensure_onboarded(chat_id: int, user: User) -> bool:
    """
    Проверяет, что пользователь прошёл онбординг.
    Если нет — сам показывает нужный шаг и возвращает False.
    """
    if user.language is None:
        bot.send_message(
            chat_id,
            "Выберите язык / Choose language / Sprache wählen / Choisissez la langue:",
            reply_markup=ClientKeyboards.language_choice(),
        )
        return False

    if not user.age_confirmed:
        bot.send_message(
            chat_id,
            t.get("age_confirm_title", user.language),
            reply_markup=ClientKeyboards.age_confirm(user.language),
        )
        return False

    return True


# ---------- /start ----------

@bot.message_handler(commands=["start"])
def cmd_start(message: Message) -> None:
    user = get_user(message.from_user.id, message.from_user.username)

    if not ensure_onboarded(message.chat.id, user):
        return

    name = message.from_user.username or message.from_user.first_name
    bot.send_message(
        chat_id=message.chat.id,
        text=t.get("welcome", user.language).format(name=name),
        reply_markup=ClientKeyboards.main_menu(user.language),
    )


# ---------- онбординг: язык и возраст ----------

@bot.callback_query_handler(func=lambda c: c.data.startswith("lang:"))
def set_language(callback: CallbackQuery) -> None:
    code = callback.data.split(":")[1]
    lang = Language(code)

    with database.session() as session:
        repo = UserRepository(session)
        repo.get_or_create(callback.from_user.id, callback.from_user.username)
        repo.set_language(callback.from_user.id, lang)
        session.commit()

    user = get_user(callback.from_user.id, callback.from_user.username)
    bot.answer_callback_query(callback.id, "OK")

    # удаляем сообщение с выбором языка и продолжаем онбординг
    try:
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except Exception:
        pass

    if not ensure_onboarded(callback.message.chat.id, user):
        return

    name = callback.from_user.username or callback.from_user.first_name
    bot.send_message(
        chat_id=callback.message.chat.id,
        text=t.get("welcome", user.language).format(name=name),
        reply_markup=ClientKeyboards.main_menu(user.language),
    )


@bot.callback_query_handler(func=lambda c: c.data == "change_lang")
def change_language(callback: CallbackQuery) -> None:
    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Выберите язык / Choose language:",
        reply_markup=ClientKeyboards.language_choice(),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data == "age:yes")
def age_confirm_yes(callback: CallbackQuery) -> None:
    with database.session() as session:
        UserRepository(session).confirm_age(callback.from_user.id)
        session.commit()

    user = get_user(callback.from_user.id, callback.from_user.username)
    try:
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except Exception:
        pass

    name = callback.from_user.username or callback.from_user.first_name
    bot.send_message(
        chat_id=callback.message.chat.id,
        text=t.get("welcome", user.language).format(name=name),
        reply_markup=ClientKeyboards.main_menu(user.language),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data == "age:no")
def age_confirm_no(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id, callback.from_user.username)
    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=t.get("age_denied", user.language),
    )
    bot.answer_callback_query(callback.id)


# ---------- каталог ----------

@bot.callback_query_handler(func=lambda c: c.data == "catalog")
def show_catalog(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id, callback.from_user.username)
    if not ensure_onboarded(callback.message.chat.id, user):
        bot.answer_callback_query(callback.id)
        return

    with database.session() as session:
        products = ProductRepository(session).get_all()

    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Выберите вкус:",
        reply_markup=ClientKeyboards.catalog(products, user.language),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("product:"))
def show_product(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id, callback.from_user.username)
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

    markup = ClientKeyboards.product_card(product.id, user.language)
    if product.photo_file_id:
        try:
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except Exception:
            pass
        bot.send_photo(
            callback.message.chat.id,
            photo=product.photo_file_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=markup,
        )
    else:
        safe_edit_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            parse_mode="HTML",
            reply_markup=markup,
        )
    bot.answer_callback_query(callback.id)


# ---------- покупка: выбор количества ----------

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy:"))
def choose_quantity(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id, callback.from_user.username)
    if not ensure_onboarded(callback.message.chat.id, user):
        bot.answer_callback_query(callback.id)
        return

    product_id = int(callback.data.split(":")[1])

    with database.session() as session:
        product = ProductRepository(session).get_by_id(product_id)

    if product is None or product.stock == 0:
        bot.answer_callback_query(callback.id, "Нет в наличии", show_alert=True)
        return

    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"Сколько штук <b>{product.flavor}</b> добавить в корзину?",
        parse_mode="HTML",
        reply_markup=ClientKeyboards.quantity_picker(product.id, product.stock, user.language),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("qty:"))
def add_to_cart(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id, callback.from_user.username)
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

    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=render_cart_text(cart, user.language),
        parse_mode="HTML",
        reply_markup=ClientKeyboards.cart_actions(user.language),
    )
    bot.answer_callback_query(callback.id, f"Добавлено: {qty} шт")


# ---------- корзина ----------

@bot.callback_query_handler(func=lambda c: c.data == "cart")
def show_cart(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id, callback.from_user.username)
    if not ensure_onboarded(callback.message.chat.id, user):
        bot.answer_callback_query(callback.id)
        return

    cart = load_cart(callback.from_user.id, callback.message.chat.id)
    kb = (
        ClientKeyboards.cart_actions(user.language)
        if not cart.is_empty
        else ClientKeyboards.empty_cart(user.language)
    )

    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=render_cart_text(cart, user.language),
        parse_mode="HTML",
        reply_markup=kb,
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data == "cart_clear")
def clear_cart(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id, callback.from_user.username)
    cart = Cart()
    save_cart(callback.from_user.id, callback.message.chat.id, cart)
    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="🗑 Корзина очищена",
        reply_markup=ClientKeyboards.empty_cart(user.language),
    )
    bot.answer_callback_query(callback.id, "Корзина очищена")


# ---------- оформление: старт ----------

@bot.callback_query_handler(func=lambda c: c.data == "checkout")
def checkout_start(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id, callback.from_user.username)
    if not ensure_onboarded(callback.message.chat.id, user):
        bot.answer_callback_query(callback.id)
        return

    cart = load_cart(callback.from_user.id, callback.message.chat.id)
    if cart.is_empty:
        bot.answer_callback_query(callback.id, "Корзина пуста", show_alert=True)
        return

    bot.set_state(callback.from_user.id, CheckoutStates.delivery_type, callback.message.chat.id)
    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Как получите заказ?",
        reply_markup=ClientKeyboards.delivery_choice(user.language),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("dtype:"))
def choose_delivery_type(callback: CallbackQuery) -> None:
    dtype = callback.data.split(":")[1]
    with bot.retrieve_data(callback.from_user.id, callback.message.chat.id) as data:
        data["delivery_type"] = dtype

    bot.set_state(callback.from_user.id, CheckoutStates.client_name, callback.message.chat.id)
    bot.send_message(callback.message.chat.id, "Как вас зовут?")
    bot.answer_callback_query(callback.id)


# ---------- сбор данных ----------

@bot.message_handler(state=CheckoutStates.client_name)
def get_client_name(message: Message) -> None:
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["client_name"] = message.text.strip()

    bot.set_state(message.from_user.id, CheckoutStates.phone, message.chat.id)
    bot.send_message(message.chat.id, "Ваш телефон (в формате +41...)?")


@bot.message_handler(state=CheckoutStates.phone)
def get_phone(message: Message) -> None:
    phone = message.text.strip()
    if len(phone) < 7:
        bot.send_message(message.chat.id, "Похоже, номер слишком короткий. Введите ещё раз.")
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["phone"] = phone
        dtype = data.get("delivery_type")

    if dtype == "delivery":
        bot.set_state(message.from_user.id, CheckoutStates.address, message.chat.id)
        bot.send_message(message.chat.id, "Адрес доставки (улица, дом)?")
    else:
        user = get_user(message.from_user.id, message.from_user.username)
        bot.set_state(message.from_user.id, CheckoutStates.pickup_time, message.chat.id)
        bot.send_message(
            message.chat.id,
            t.get("pickup_location", user.language).format(link=PICKUP_ADDRESS_LINK)
            + "\n\nКогда вам удобно забрать заказ?",
        )


@bot.message_handler(state=CheckoutStates.address)
def get_address(message: Message) -> None:
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["address"] = message.text.strip()

    bot.set_state(message.from_user.id, CheckoutStates.city, message.chat.id)
    bot.send_message(message.chat.id, "Город?")


@bot.message_handler(state=CheckoutStates.city)
def get_city(message: Message) -> None:
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["city"] = message.text.strip()

    bot.set_state(message.from_user.id, CheckoutStates.zip_code, message.chat.id)
    bot.send_message(message.chat.id, "Почтовый индекс?")


@bot.message_handler(state=CheckoutStates.zip_code)
def get_zip(message: Message) -> None:
    user = get_user(message.from_user.id, message.from_user.username)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["zip_code"] = message.text.strip()

    bot.set_state(message.from_user.id, CheckoutStates.comment, message.chat.id)
    bot.send_message(
        message.chat.id,
        "Комментарий к заказу (или нажмите «Пропустить»)?",
        reply_markup=ClientKeyboards.skip_comment(user.language),
    )


@bot.message_handler(state=CheckoutStates.pickup_time)
def get_pickup_time(message: Message) -> None:
    user = get_user(message.from_user.id, message.from_user.username)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["pickup_time"] = message.text.strip()

    bot.set_state(message.from_user.id, CheckoutStates.comment, message.chat.id)
    bot.send_message(
        message.chat.id,
        "Комментарий к заказу (или нажмите «Пропустить»)?",
        reply_markup=ClientKeyboards.skip_comment(user.language),
    )


@bot.message_handler(state=CheckoutStates.comment)
def get_comment(message: Message) -> None:
    user = get_user(message.from_user.id, message.from_user.username)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["comment"] = message.text.strip()
    show_confirmation(message.chat.id, message.from_user.id, user.language)


@bot.callback_query_handler(func=lambda c: c.data == "skip_comment")
def skip_comment(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id, callback.from_user.username)
    with bot.retrieve_data(callback.from_user.id, callback.message.chat.id) as data:
        data["comment"] = None
    bot.answer_callback_query(callback.id)
    show_confirmation(callback.message.chat.id, callback.from_user.id, user.language)


# ---------- подтверждение ----------

def show_confirmation(chat_id: int, user_id: int, lang: Language | None = None) -> None:
    cart = load_cart(user_id, chat_id)

    with bot.retrieve_data(user_id, chat_id) as data:
        dtype = data.get("delivery_type")
        name = data.get("client_name")
        phone = data.get("phone")
        address = data.get("address")
        city = data.get("city")
        zip_code = data.get("zip_code")
        pickup_time = data.get("pickup_time")
        comment = data.get("comment")

    delivery = DeliveryCalculator.calculate(cart.total_quantity, dtype)
    total = cart.items_sum + delivery

    lines = ["📋 <b>Проверьте заказ:</b>\n"]
    for item in cart.items.values():
        lines.append(f"{item.flavor} — {item.quantity} шт × {item.price} = {item.subtotal} CHF")

    delivery_str = "бесплатно" if delivery == 0 else f"{delivery} CHF"
    lines.append(f"\nСумма товаров: {cart.items_sum} CHF")
    lines.append(f"Доставка: {delivery_str}")
    lines.append(f"<b>Итого: {total} CHF</b>\n")

    lines.append(f"Имя: {name}")
    lines.append(f"Телефон: {phone}")
    if dtype == "delivery":
        lines.append(f"Адрес: {address}, {city}, {zip_code}")
    else:
        lines.append(f"Самовывоз, время: {pickup_time}")
    if comment:
        lines.append(f"Комментарий: {comment}")

    bot.set_state(user_id, CheckoutStates.confirm, chat_id)
    bot.send_message(
        chat_id,
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=ClientKeyboards.confirm_order(lang),
    )


@bot.callback_query_handler(func=lambda c: c.data == "order_confirm")
def confirm_order(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    user = get_user(user_id, callback.from_user.username)
    cart = load_cart(user_id, chat_id)

    with bot.retrieve_data(user_id, chat_id) as data:
        dtype = DeliveryType(data.get("delivery_type"))
        name = data.get("client_name")
        phone = data.get("phone")
        address = data.get("address")
        city = data.get("city")
        zip_code = data.get("zip_code")
        pickup_time = data.get("pickup_time")
        comment = data.get("comment")

    try:
        with database.session() as session:
            service = OrderService(session)
            order = service.create_order(
                cart=cart,
                tg_user_id=user_id,
                tg_username=callback.from_user.username,
                client_name=name,
                phone=phone,
                delivery_type=dtype,
                address=address,
                city=city,
                zip_code=zip_code,
                pickup_time=pickup_time,
                comment=comment,
            )
            notifier.notify_new_order(order)
            order_id = order.id
    except ValueError as e:
        bot.answer_callback_query(callback.id, f"Ошибка: {e}", show_alert=True)
        return

    # чистим корзину и состояние
    save_cart(user_id, chat_id, Cart())
    bot.delete_state(user_id, chat_id)

    text = t.get("order_accepted_cash", user.language).format(order_id=order_id)
    if dtype == DeliveryType.PICKUP:
        text += "\n\n" + t.get("pickup_location", user.language).format(link=PICKUP_ADDRESS_LINK)

    safe_edit_message(
        chat_id=chat_id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=ClientKeyboards.main_menu(user.language),
    )
    bot.answer_callback_query(callback.id, "Заказ создан")


@bot.callback_query_handler(func=lambda c: c.data == "order_cancel")
def cancel_order(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id, callback.from_user.username)
    bot.delete_state(callback.from_user.id, callback.message.chat.id)
    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Заказ отменён. Корзина сохранена.",
        reply_markup=ClientKeyboards.main_menu(user.language),
    )
    bot.answer_callback_query(callback.id)


# ---------- админ-панель ----------

@bot.message_handler(commands=["admin"], is_admin=True)
def admin_panel_cmd(message: Message) -> None:
    bot.send_message(
        message.chat.id,
        "👑 <b>Админ-панель</b>",
        parse_mode="HTML",
        reply_markup=AdminKeyboards.panel(),
    )


@bot.message_handler(commands=["admin"])
def admin_denied(message: Message) -> None:
    bot.send_message(message.chat.id, "У вас нет доступа.")


@bot.callback_query_handler(func=lambda c: c.data == "admin:panel", is_admin=True)
def admin_panel_back(callback: CallbackQuery) -> None:
    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="👑 <b>Админ-панель</b>",
        parse_mode="HTML",
        reply_markup=AdminKeyboards.panel(),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data == "admin:finance", is_admin=True)
def admin_finance(callback: CallbackQuery) -> None:
    with database.session() as session:
        summary = FinanceRepository(session).summary()

    text = (
        "💰 <b>Финансовый отчёт</b>\n\n"
        f"Оплаченных заказов: <b>{summary['orders_count']}</b>\n"
        f"Сумма товаров: <b>{summary['items_sum']} CHF</b>\n"
        f"Доставка получена: <b>{summary['delivery_sum']} CHF</b>\n"
        f"Итого оплачено клиентами: <b>{summary['total_paid']} CHF</b>\n\n"
        f"Комиссия посредника: <b>{summary['commission_sum']} CHF</b>\n"
        f"Сумма после комиссии: <b>{summary['after_commission']} CHF</b>\n\n"
        f"Средний чек: <b>{summary['avg_check']:.2f} CHF</b>"
    )
    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=AdminKeyboards.panel(),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data == "admin:stock", is_admin=True)
def admin_stock(callback: CallbackQuery) -> None:
    with database.session() as session:
        products = ProductRepository(session).get_all()

    lines = ["📦 <b>Остатки:</b>\n"]
    for p in products:
        emoji = "✅" if p.stock > 0 else "❌"
        lines.append(f"{emoji} {p.flavor}: {p.stock} шт")

    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="\n".join(lines),
        parse_mode="HTML",
        reply_markup=AdminKeyboards.panel(),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data == "admin:flavors", is_admin=True)
def admin_flavors(callback: CallbackQuery) -> None:
    with database.session() as session:
        stats = OrderRepository(session).flavor_stats()

    if not stats:
        text = "🍬 <b>Отчёт по вкусам</b>\n\nПока нет оплаченных заказов."
    else:
        total = sum(qty for _, qty in stats)
        lines = ["🍬 <b>Отчёт по вкусам</b>\n", f"Всего продано: <b>{total}</b> шт\n"]
        for flavor, qty in stats:
            pct = (qty / total) * 100
            lines.append(f"{flavor} — {qty} шт / {pct:.1f}%")
        top_flavor = stats[0][0]
        lines.append(f"\n🏆 Самый популярный: <b>{top_flavor}</b>")
        text = "\n".join(lines)

    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=AdminKeyboards.panel(),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data == "admin:orders", is_admin=True)
def admin_orders(callback: CallbackQuery) -> None:
    with database.session() as session:
        orders = OrderRepository(session).list_recent(limit=10)

    if not orders:
        safe_edit_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="📋 Заказов пока нет.",
            reply_markup=AdminKeyboards.panel(),
        )
        bot.answer_callback_query(callback.id)
        return

    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="📋 <b>Последние заказы:</b>",
        parse_mode="HTML",
        reply_markup=AdminKeyboards.orders_list(orders),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("admin:order:"), is_admin=True)
def admin_order_detail(callback: CallbackQuery) -> None:
    order_id = int(callback.data.split(":")[2])

    with database.session() as session:
        order = OrderRepository(session).get_by_id(order_id)
        if order is None:
            bot.answer_callback_query(callback.id, "Заказ не найден", show_alert=True)
            return

        # свежая выборка возвращает статусы как обычные строки, а не enum — нормализуем
        delivery_type = DeliveryType(order.delivery_type)
        order_status = OrderStatus(order.order_status)
        payment_status = PaymentStatus(order.payment_status)

        lines = [f"📋 <b>Заказ #{order.id}</b>\n"]
        lines.append(f"Клиент: {order.client_name}")
        lines.append(f"Телефон: {order.phone}")
        lines.append(f"Тип: {delivery_type.value}")
        if delivery_type == DeliveryType.DELIVERY:
            lines.append(f"Адрес: {order.address}, {order.city}, {order.zip_code}")
        else:
            lines.append(f"Самовывоз: {order.pickup_time}")
        lines.append(f"\nСумма: {order.total_sum} CHF")
        lines.append(f"Статус заказа: <b>{order_status.value}</b>")
        lines.append(f"Статус оплаты: <b>{payment_status.value}</b>")

        lines.append("\n<b>Позиции:</b>")
        for item in order.items:
            lines.append(f"{item.flavor} — {item.quantity} × {item.price_per_item} CHF")

    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="\n".join(lines),
        parse_mode="HTML",
        reply_markup=AdminKeyboards.order_actions(order_id),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("admin:status:"), is_admin=True)
def admin_status_menu(callback: CallbackQuery) -> None:
    order_id = int(callback.data.split(":")[2])
    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Выберите новый статус:",
        reply_markup=AdminKeyboards.status_choice(order_id),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("admin:setstatus:"), is_admin=True)
def admin_set_status(callback: CallbackQuery) -> None:
    _, _, order_id_str, status_value = callback.data.split(":")
    order_id = int(order_id_str)
    new_status = OrderStatus(status_value)

    with database.session() as session:
        order = OrderRepository(session).update_status(order_id, new_status)
        if order is None:
            bot.answer_callback_query(callback.id, "Заказ не найден", show_alert=True)
            return
        client_tg = order.tg_user_id
        session.commit()

    # уведомляем клиента
    try:
        bot.send_message(
            client_tg,
            f"📦 Статус вашего заказа #{order_id} изменён: <b>{new_status.value}</b>",
            parse_mode="HTML",
        )
    except Exception:
        pass  # клиент мог заблокировать бота

    bot.answer_callback_query(callback.id, f"Статус изменён: {new_status.value}")
    # возвращаемся к карточке заказа
    admin_order_detail(callback)


@bot.callback_query_handler(func=lambda c: c.data.startswith("admin:meettime:"), is_admin=True)
def admin_meet_time_start(callback: CallbackQuery) -> None:
    order_id = int(callback.data.split(":")[2])

    with bot.retrieve_data(callback.from_user.id, callback.message.chat.id) as data:
        data["meet_time_order_id"] = order_id

    bot.set_state(callback.from_user.id, AdminStates.set_meet_time, callback.message.chat.id)
    bot.send_message(callback.message.chat.id, "Введите время и место встречи для отправки клиенту:")
    bot.answer_callback_query(callback.id)


@bot.message_handler(state=AdminStates.set_meet_time, is_admin=True)
def admin_apply_meet_time(message: Message) -> None:
    meet_time = message.text.strip()

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        order_id = data.get("meet_time_order_id")

    with database.session() as session:
        order = OrderRepository(session).get_by_id(order_id)
        if order is None:
            bot.delete_state(message.from_user.id, message.chat.id)
            bot.send_message(message.chat.id, "Заказ не найден.")
            return
        client_tg = order.tg_user_id
        client_user = session.get(User, client_tg)
        client_lang = client_user.language if client_user else None

    bot.delete_state(message.from_user.id, message.chat.id)

    try:
        bot.send_message(
            client_tg,
            t.get("meet_time_notice", client_lang).format(order_id=order_id, time=meet_time),
            parse_mode="HTML",
        )
    except Exception:
        bot.send_message(
            message.chat.id,
            "⚠️ Не удалось отправить клиенту (возможно, заблокировал бота).",
        )
        return

    bot.send_message(message.chat.id, f"✅ Время встречи отправлено клиенту по заказу #{order_id}.")


@bot.callback_query_handler(func=lambda c: c.data == "admin:edit_product", is_admin=True)
def admin_edit_product_list(callback: CallbackQuery) -> None:
    with database.session() as session:
        products = ProductRepository(session).get_all()

    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="✏️ Выберите товар для редактирования:",
        reply_markup=AdminKeyboards.products_list(products),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("admin:product:"), is_admin=True)
def admin_product_card(callback: CallbackQuery) -> None:
    product_id = int(callback.data.split(":")[2])

    with database.session() as session:
        product = ProductRepository(session).get_by_id(product_id)
        if product is None:
            bot.answer_callback_query(callback.id, "Товар не найден", show_alert=True)
            return

        text = (
            f"✏️ <b>{product.flavor}</b>\n\n"
            f"Цена: {product.price} CHF\n"
            f"Остаток: {product.stock} шт\n"
            f"Описание: {product.description}"
        )

    safe_edit_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=AdminKeyboards.product_edit_actions(product_id),
    )
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("admin:pedit:"), is_admin=True)
def admin_start_edit(callback: CallbackQuery) -> None:
    _, _, field, product_id_str = callback.data.split(":")
    product_id = int(product_id_str)

    with bot.retrieve_data(callback.from_user.id, callback.message.chat.id) as data:
        data["edit_product_id"] = product_id

    prompts = {
        "price": ("Введите новую цену в CHF (например: 22.00):", AdminStates.edit_price),
        "stock": ("Введите новый остаток (целое число):", AdminStates.edit_stock),
        "desc": ("Введите новое описание:", AdminStates.edit_desc),
        "photo": ("Пришлите фото товара:", AdminStates.edit_photo),
    }
    prompt, state = prompts[field]
    bot.set_state(callback.from_user.id, state, callback.message.chat.id)
    bot.send_message(callback.message.chat.id, prompt)
    bot.answer_callback_query(callback.id)


@bot.message_handler(state=AdminStates.edit_price, is_admin=True)
def admin_apply_price(message: Message) -> None:
    from decimal import Decimal, InvalidOperation

    try:
        new_price = Decimal(message.text.strip().replace(",", "."))
        if new_price <= 0:
            raise InvalidOperation
    except InvalidOperation:
        bot.send_message(message.chat.id, "Некорректная цена. Введите число, например 22.00")
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        product_id = data.get("edit_product_id")

    with database.session() as session:
        product = ProductRepository(session).get_by_id(product_id)
        if product is not None:
            product.price = new_price
            session.commit()

    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, f"✅ Цена обновлена: {new_price} CHF")


@bot.message_handler(state=AdminStates.edit_stock, is_admin=True)
def admin_apply_stock(message: Message) -> None:
    try:
        new_stock = int(message.text.strip())
        if new_stock < 0:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "Некорректное число. Введите целое, например 15")
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        product_id = data.get("edit_product_id")

    with database.session() as session:
        product = ProductRepository(session).get_by_id(product_id)
        if product is not None:
            product.stock = new_stock
            session.commit()

    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, f"✅ Остаток обновлён: {new_stock} шт")


@bot.message_handler(state=AdminStates.edit_desc, is_admin=True)
def admin_apply_desc(message: Message) -> None:
    new_desc = message.text.strip()
    if not new_desc:
        bot.send_message(message.chat.id, "Описание не может быть пустым.")
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        product_id = data.get("edit_product_id")

    with database.session() as session:
        product = ProductRepository(session).get_by_id(product_id)
        if product is not None:
            product.description = new_desc
            session.commit()

    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, "✅ Описание обновлено")


@bot.message_handler(state=AdminStates.edit_photo, is_admin=True, content_types=["photo"])
def admin_apply_photo(message: Message) -> None:
    file_id = message.photo[-1].file_id

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        product_id = data.get("edit_product_id")

    with database.session() as session:
        product = ProductRepository(session).get_by_id(product_id)
        if product is not None:
            product.photo_file_id = file_id
            session.commit()

    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, "✅ Фото обновлено")


@bot.message_handler(state=AdminStates.edit_photo, is_admin=True)
def admin_apply_photo_wrong_type(message: Message) -> None:
    bot.send_message(message.chat.id, "Пришлите именно фото (не файл и не текст).")


# ---------- полная статистика по заказам ----------

ORDER_STATUS_LABELS: dict[str, str] = {
    OrderStatus.NEW.value: "🆕 Новый",
    OrderStatus.WAITING_PAYMENT.value: "⏳ Ожидает оплаты",
    OrderStatus.PAID.value: "💰 Оплачено",
    OrderStatus.ASSEMBLING.value: "📦 Собирается",
    OrderStatus.READY.value: "✅ Готов к выдаче",
    OrderStatus.IN_DELIVERY.value: "🚚 В доставке",
    OrderStatus.COMPLETED.value: "🎉 Выдан",
    OrderStatus.CANCELLED.value: "❌ Отменён",
}


@bot.message_handler(commands=["admin-7355608"], is_admin=True)
def admin_full_stats(message: Message) -> None:
    with database.session() as session:
        order_repo = OrderRepository(session)
        total_orders = order_repo.count_all()
        status_counts = order_repo.status_counts()
        flavor_stats = order_repo.flavor_stats()
        finance = FinanceRepository(session).summary()
        products = ProductRepository(session).get_all()

    lines = ["📊 <b>Полная статистика по заказам</b>\n"]

    lines.append(f"Всего заказов: <b>{total_orders}</b>\n")
    lines.append("<b>По статусам:</b>")
    for status_value, label in ORDER_STATUS_LABELS.items():
        lines.append(f"{label} — {status_counts.get(status_value, 0)}")

    lines.append("\n🍬 <b>Отчёт по вкусам</b> (по оплаченным заказам)")
    if not flavor_stats:
        lines.append("Пока нет оплаченных заказов.")
    else:
        stock_by_flavor = {p.flavor: p.stock for p in products}
        total_sold = sum(qty for _, qty in flavor_stats)
        lines.append(f"Всего продано: <b>{total_sold}</b> шт")
        for flavor, qty in flavor_stats:
            pct = (qty / total_sold) * 100
            stock_left = stock_by_flavor.get(flavor, "?")
            lines.append(f"{flavor} — {qty} шт / {pct:.1f}% (остаток: {stock_left})")
        lines.append(f"🏆 Самый популярный: <b>{flavor_stats[0][0]}</b>")

    lines.append("\n💰 <b>Финансы</b>")
    lines.append(f"Оплаченных заказов: <b>{finance['orders_count']}</b>")
    lines.append(f"Сумма товаров: <b>{finance['items_sum']} CHF</b>")
    lines.append(f"Доставка получена: <b>{finance['delivery_sum']} CHF</b>")
    lines.append(f"Итого оплачено клиентами: <b>{finance['total_paid']} CHF</b>")
    lines.append(f"Комиссия посредника: <b>{finance['commission_sum']} CHF</b>")
    lines.append(f"Сумма после комиссии: <b>{finance['after_commission']} CHF</b>")
    lines.append(f"Средний чек: <b>{finance['avg_check']:.2f} CHF</b>")

    lines.append("\n📦 <b>Остатки товаров</b>")
    for p in products:
        emoji = "✅" if p.stock > 0 else "❌"
        lines.append(f"{emoji} {p.flavor}: {p.stock} шт")

    bot.send_message(message.chat.id, "\n".join(lines), parse_mode="HTML")


# ---------- запуск ----------

if __name__ == "__main__":
    bot.add_custom_filter(StateFilter(bot))
    bot.add_custom_filter(IsAdminFilter(ADMIN_IDS))
    print("bot was started!")
    bot.infinity_polling()