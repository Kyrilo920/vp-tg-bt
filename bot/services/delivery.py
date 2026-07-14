from decimal import Decimal

class DeliveryCalculator:
    @staticmethod
    def calculate(total_quantity: int) -> Decimal:
        if total_quantity >= 5:
            return Decimal("0")
        if total_quantity >= 3:
            return Decimal("7")
        if total_quantity >= 1:
            return Decimal("10")
        return Decimal("0")
    