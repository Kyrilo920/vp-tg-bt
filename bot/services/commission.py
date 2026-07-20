from decimal import Decimal

COMMISSION_PER_UNIT: dict[Decimal, Decimal] = {
    Decimal("18.00"): Decimal("3.00"),
    Decimal("20.00"): Decimal("4.00"),
    Decimal("22.00"): Decimal("5.00"),
    Decimal("25.00"): Decimal("7.00"),
    Decimal("30.00"): Decimal("7.00"),
}


class CommissionCalculator:
    @staticmethod
    def for_line(price: Decimal, quantity: int) -> Decimal:
        commission = COMMISSION_PER_UNIT.get(price)
        if commission is None:
            raise ValueError(f"Не настроена комиссия для цены {price} CHF")
        return commission * quantity
