from decimal import Decimal

from app.billing.invoices import LineItem, calculate_invoice_total


def test_calculate_invoice_total_applies_tax_and_discount() -> None:
    total = calculate_invoice_total([LineItem("seat", Decimal("10.00"), 2)], Decimal("3.00"))
    assert total == Decimal("18.6000")
