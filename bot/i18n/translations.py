from bot.db.models.user import Language


TRANSLATIONS: dict[Language, dict[str, str]] = {
    Language.RU: {
        "welcome": "Привет, {name}!\n\nЯ бот-магазин UZY 15K. Открой каталог, чтобы посмотреть вкусы.",
        "choose_language": "Выберите язык:",
        "age_confirm_title": "Подтвердите, что вам есть 18 лет или больше.",
        "age_yes": "✅ Да, мне 18+",
        "age_no": "❌ Нет",
        "age_denied": "К сожалению, каталог доступен только с 18 лет.",
        "pickup_location": "📍 Адрес самовывоза: {link}",
        "menu_catalog": "🛒 Каталог",
        "menu_cart": "🧺 Корзина",
        "menu_change_lang": "🌐 Сменить язык",
        "cart_empty": "🧺 Корзина пуста",
        "your_cart": "🧺 <b>Ваша корзина:</b>",
        "total_items": "Всего товаров",
        "items_sum": "Сумма товаров",
        "delivery": "Доставка",
        "delivery_free": "бесплатно 🎁",
        "total": "Итого",
        "btn_buy": "🛒 Купить",
        "btn_back": "⬅️ Назад",
        "btn_cancel": "⬅️ Отмена",
        "btn_add_more": "➕ Добавить ещё товар",
        "btn_clear_cart": "🗑 Очистить корзину",
        "btn_checkout": "✅ Оформить заказ",
        "btn_to_catalog": "🛒 В каталог",
        "btn_delivery": "🚚 Доставка",
        "btn_pickup": "🏪 Самовывоз",
        "btn_back_to_cart": "⬅️ Назад в корзину",
        "btn_skip": "Пропустить",
        "btn_confirm_order": "✅ Подтвердить заказ",
        "btn_cancel_order": "❌ Отменить",
        "order_accepted_cash": (
            "✅ Заказ #{order_id} принят!\n\n"
            "💵 Оплата наличными при получении заказа на вокзале в Фрибурге."
        ),
        "meet_time_notice": (
            "🕐 <b>Время и место встречи для заказа #{order_id}:</b>\n\n{time}"
        ),
    },
    Language.EN: {
        "welcome": "Hi, {name}!\n\nI'm the UZY 15K shop bot. Open the catalog to see flavors.",
        "choose_language": "Choose language:",
        "age_confirm_title": "Please confirm that you are 18 or older.",
        "age_yes": "✅ Yes, I'm 18+",
        "age_no": "❌ No",
        "age_denied": "Sorry, the catalog is only available to those 18+.",
        "pickup_location": "📍 Pickup address: {link}",
        "menu_catalog": "🛒 Catalog",
        "menu_cart": "🧺 Cart",
        "menu_change_lang": "🌐 Change language",
        "cart_empty": "🧺 Your cart is empty",
        "your_cart": "🧺 <b>Your cart:</b>",
        "total_items": "Total items",
        "items_sum": "Items subtotal",
        "delivery": "Delivery",
        "delivery_free": "free 🎁",
        "total": "Total",
        "btn_buy": "🛒 Buy",
        "btn_back": "⬅️ Back",
        "btn_cancel": "⬅️ Cancel",
        "btn_add_more": "➕ Add more",
        "btn_clear_cart": "🗑 Clear cart",
        "btn_checkout": "✅ Checkout",
        "btn_to_catalog": "🛒 To catalog",
        "btn_delivery": "🚚 Delivery",
        "btn_pickup": "🏪 Pickup",
        "btn_back_to_cart": "⬅️ Back to cart",
        "btn_skip": "Skip",
        "btn_confirm_order": "✅ Confirm order",
        "btn_cancel_order": "❌ Cancel",
        "order_accepted_cash": (
            "✅ Order #{order_id} accepted!\n\n"
            "💵 Payment in cash on pickup at the Fribourg train station."
        ),
        "meet_time_notice": (
            "🕐 <b>Meeting time and place for order #{order_id}:</b>\n\n{time}"
        ),
    },
    Language.DE: {
        "welcome": "Hallo, {name}!\n\nIch bin der UZY 15K Shop-Bot. Öffne den Katalog, um die Geschmacksrichtungen zu sehen.",
        "choose_language": "Sprache wählen:",
        "age_confirm_title": "Bitte bestätige, dass du 18 Jahre oder älter bist.",
        "age_yes": "✅ Ja, ich bin 18+",
        "age_no": "❌ Nein",
        "age_denied": "Der Katalog ist leider nur für Personen ab 18 verfügbar.",
        "pickup_location": "📍 Abholadresse: {link}",
        "menu_catalog": "🛒 Katalog",
        "menu_cart": "🧺 Warenkorb",
        "menu_change_lang": "🌐 Sprache ändern",
        "cart_empty": "🧺 Der Warenkorb ist leer",
        "your_cart": "🧺 <b>Dein Warenkorb:</b>",
        "total_items": "Artikel insgesamt",
        "items_sum": "Zwischensumme",
        "delivery": "Lieferung",
        "delivery_free": "kostenlos 🎁",
        "total": "Gesamt",
        "btn_buy": "🛒 Kaufen",
        "btn_back": "⬅️ Zurück",
        "btn_cancel": "⬅️ Abbrechen",
        "btn_add_more": "➕ Mehr hinzufügen",
        "btn_clear_cart": "🗑 Warenkorb leeren",
        "btn_checkout": "✅ Zur Kasse",
        "btn_to_catalog": "🛒 Zum Katalog",
        "btn_delivery": "🚚 Lieferung",
        "btn_pickup": "🏪 Abholung",
        "btn_back_to_cart": "⬅️ Zurück zum Warenkorb",
        "btn_skip": "Überspringen",
        "btn_confirm_order": "✅ Bestellung bestätigen",
        "btn_cancel_order": "❌ Abbrechen",
        "order_accepted_cash": (
            "✅ Bestellung #{order_id} angenommen!\n\n"
            "💵 Barzahlung bei Abholung am Bahnhof Freiburg."
        ),
        "meet_time_notice": (
            "🕐 <b>Treffpunkt und Uhrzeit für Bestellung #{order_id}:</b>\n\n{time}"
        ),
    },
    Language.FR: {
        "welcome": "Salut, {name}!\n\nJe suis le bot boutique UZY 15K. Ouvre le catalogue pour voir les saveurs.",
        "choose_language": "Choisissez la langue:",
        "age_confirm_title": "Veuillez confirmer que vous avez 18 ans ou plus.",
        "age_yes": "✅ Oui, j'ai 18+",
        "age_no": "❌ Non",
        "age_denied": "Désolé, le catalogue est réservé aux personnes de 18 ans et plus.",
        "pickup_location": "📍 Adresse de retrait : {link}",
        "menu_catalog": "🛒 Catalogue",
        "menu_cart": "🧺 Panier",
        "menu_change_lang": "🌐 Changer de langue",
        "cart_empty": "🧺 Votre panier est vide",
        "your_cart": "🧺 <b>Votre panier :</b>",
        "total_items": "Total articles",
        "items_sum": "Sous-total",
        "delivery": "Livraison",
        "delivery_free": "gratuit 🎁",
        "total": "Total",
        "btn_buy": "🛒 Acheter",
        "btn_back": "⬅️ Retour",
        "btn_cancel": "⬅️ Annuler",
        "btn_add_more": "➕ Ajouter encore",
        "btn_clear_cart": "🗑 Vider le panier",
        "btn_checkout": "✅ Passer la commande",
        "btn_to_catalog": "🛒 Vers le catalogue",
        "btn_delivery": "🚚 Livraison",
        "btn_pickup": "🏪 Retrait",
        "btn_back_to_cart": "⬅️ Retour au panier",
        "btn_skip": "Passer",
        "btn_confirm_order": "✅ Confirmer la commande",
        "btn_cancel_order": "❌ Annuler",
        "order_accepted_cash": (
            "✅ Commande #{order_id} acceptée !\n\n"
            "💵 Paiement en espèces à la remise de la commande à la gare de Fribourg."
        ),
        "meet_time_notice": (
            "🕐 <b>Heure et lieu de rendez-vous pour la commande #{order_id} :</b>\n\n{time}"
        ),
    },
}


class Translator:
    """Простой i18n: возвращает текст по ключу и языку."""

    DEFAULT = Language.RU

    def __init__(self, translations: dict = TRANSLATIONS) -> None:
        self._t = translations

    def get(self, key: str, language: Language | None) -> str:
        lang = language or self.DEFAULT
        # если ключа нет в выбранном языке — падаем на RU
        return self._t[lang].get(key) or self._t[self.DEFAULT].get(key, key)


t = Translator()
