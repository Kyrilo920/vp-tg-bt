from telebot.handler_backends import State, StatesGroup


class CartStates(StatesGroup):
    waiting_quantity = State()


class CheckoutStates(StatesGroup):
    stickerpack = State()
    delivery_type = State()
    client_name = State()
    phone = State()
    address = State()
    city = State()
    zip_code = State()
    pickup_time = State()
    comment = State()
    confirm = State()


class AdminStates(StatesGroup):
    edit_price = State()
    edit_stock = State()
    edit_desc = State()
    set_meet_time = State()