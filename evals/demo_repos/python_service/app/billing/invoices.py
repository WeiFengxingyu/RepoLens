from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LineItem:
    description: str
    unit_price: Decimal
    quantity: int

    @property
    def total(self) -> Decimal:
        return self.unit_price * self.quantity


def calculate_invoice_total(items: list[LineItem], discount: Decimal) -> Decimal:
    discount = max(discount, Decimal("0"))
    subtotal = sum(item.total for item in items)
    tax = subtotal * Decimal("0.08")
    return subtotal + tax - discount
