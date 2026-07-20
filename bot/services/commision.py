from decimal import Decimal


class CommissionCalculator:
    """Комиссия посредника — фиксированная по цене товара."""

    _RULES: dict[Decimal, Decimal] = {
        Decimal("18"): Decimal("3"),
        Decimal("20"): Decimal("4"),
        Decimal("22"): Decimal("5"),
        Decimal("25"): Decimal("7"),
        Decimal("30"): Decimal("7"),
    }

    @classmethod
    def per_item(cls, price: Decimal) -> Decimal:
        """Комиссия за 1 шт. по цене продажи."""
        return cls._RULES.get(price, Decimal("0"))

    @classmethod
    def for_line(cls, price: Decimal, quantity: int) -> Decimal:
        """Комиссия по позиции = per_item × quantity."""
        return cls.per_item(price) * quantity