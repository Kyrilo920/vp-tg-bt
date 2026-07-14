from telebot.handler_backends import State, StatesGroup

class CartStates(StatesGroup)   :
    waiting_quantity = State()
    