from dataclasses import dataclass, field 
from decimal import Decimal

@dataclass
class CartItem:
    product_id: int
    flavor: str
    price: Decimal 
    quantity: int
    
    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity

@dataclass
class Cart:
    items: dict[int, CartItem] = field(default_factory=dict)
    
    def add(self, product_id: int, flavor: str, price: Decimal, quantity: int) -> None:
        if product_id in self.items:
            self.items[product_id].quantity += quantity
        else:
            self.items[product_id] = CartItem(product_id, flavor, price, quantity)
    def remove(self, product_id: int) -> None:
        self.items.pop(product_id, None)
    
    def clear(self) -> None:
        self.items.clear()
    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.items.values())
    
    @property
    def items_sum(self) -> Decimal:
        return sum((item.subtotal for item in self.items.values()), Decimal("0"))
    
    @property
    def is_empty(self) -> bool:
        return not self.items
    
    def to_dict(self) -> dict:
        return {
            str(pid): {
                "product_id": item.product_id,
                "flavor": item.flavor,
                "price": str(item.price),
                "quantity": item.quantity,
            }
            for pid, item in self.items .items()
        }
    
    @classmethod
    def from_dict(cls, data: dict | None) -> "Cart":
        cart = cls()
        if not data:
            return cart
        for pid_str, item_data in data.items():
            cart.items[int(pid_str)] = CartItem(
                product_id=item_data["product_id"],
                flavor=item_data["flavor"],
                price=Decimal(item_data["price"]),
                quantity=item_data["quantity"],
            )
        return cart