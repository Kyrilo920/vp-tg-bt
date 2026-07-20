from telebot.custom_filters import SimpleCustomFilter
from telebot.types import Message, CallbackQuery


class IsAdminFilter(SimpleCustomFilter):
    key = "is_admin"

    def __init__(self, admin_ids: list[int]) -> None:
        self._admin_ids = admin_ids

    def check(self, obj) -> bool:
        if isinstance(obj, Message):
            return obj.from_user.id in self._admin_ids
        if isinstance(obj, CallbackQuery):
            return obj.from_user.id in self._admin_ids
        return False
