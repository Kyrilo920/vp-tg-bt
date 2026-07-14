# vape-telebot-shop

Telegram-бот-магазин на [pyTelegramBotAPI (telebot)](https://github.com/eternnoir/pyTelegramBotAPI) с каталогом товаров, корзиной и оформлением заказов. Синхронный стек: SQLAlchemy 2.0 + PostgreSQL + Alembic.

## Возможности

- Каталог вкусов (товаров) с фото, описанием и остатками на складе
- Корзина: добавление количества, пересчёт суммы, стоимость доставки
- Расчёт доставки по количеству товара (бесплатно от 5 шт, скидка от 3 шт)
- Заказы: клиент, телефон, способ получения (доставка/самовывоз), статус заказа и оплаты
- FSM-состояния через `StateMemoryStorage` (telebot)

## Стек

- Python 3.12+, [uv](https://docs.astral.sh/uv/) — управление зависимостями
- pyTelegramBotAPI
- SQLAlchemy 2.0 (sync) + psycopg2
- Alembic — миграции БД
- PostgreSQL 16 (в Docker)

## Структура проекта

```
vape-telebot-shop/
├── __main__.py              # точка входа, хендлеры бота
├── config.py                 # настройки из .env (pydantic-settings)
├── docker-compose.yml        # Postgres
├── bot/
│   ├── db/
│   │   ├── base.py            # DeclarativeBase
│   │   ├── database.py        # engine + sessionmaker
│   │   └── models/             # Product, Order, OrderItem
│   ├── domain/cart.py          # доменная логика корзины
│   ├── keyboards/client.py     # inline-клавиатуры
│   ├── repositories/           # доступ к БД (Product, Order)
│   ├── services/delivery.py    # расчёт стоимости доставки
│   └── states/cart_states.py   # FSM-состояния
├── migrations/                # Alembic
└── scripts/seed_products.py   # наполнение каталога тестовыми товарами
```

## Быстрый старт

1. Установи зависимости:
   ```bash
   uv sync
   ```
2. Скопируй `.env` и заполни:
   ```env
   BOT_TOKEN=токен_от_BotFather
   DATABASE_URL=postgresql+psycopg2://vape_user:vape_pass@localhost:5432/vape_shop
   ```
3. Подними PostgreSQL:
   ```bash
   docker compose up -d
   ```
4. Примени миграции:
   ```bash
   uv run alembic upgrade head
   ```
5. (Опционально) засей тестовые товары:
   ```bash
   uv run python -m scripts.seed_products
   ```
6. Запусти бота:
   ```bash
   uv run python __main__.py
   ```

## Миграции

Создать новую миграцию после изменения моделей:
```bash
uv run alembic revision --autogenerate -m "описание изменений"
uv run alembic upgrade head
```
