from decimal import Decimal

from bot.db.models.order import DeliveryType


class DeliveryCalculator:
    @staticmethod
    def calculate(total_quantity: int, delivery_type: DeliveryType | None = None) -> Decimal:
        if delivery_type == DeliveryType.PICKUP:
            return Decimal("0")
        if total_quantity >= 5:
            return Decimal("0")
        if total_quantity >= 3:
            return Decimal("7")
        if total_quantity >= 1:
            return Decimal("10")
        return Decimal("0")
