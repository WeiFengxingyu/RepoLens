from decimal import Decimal

from app.billing.invoices import LineItem, calculate_invoice_total
from app.repositories.invoices import InvoiceRepository


invoice_repository = InvoiceRepository()


def create_invoice(payload: dict[str, object]) -> dict[str, str]:
    """Create and persist an invoice response."""
    items = [
        LineItem(description=item["description"], unit_price=Decimal(str(item["unit_price"])), quantity=int(item["quantity"]))
        for item in payload.get("items", [])
    ]
    total = calculate_invoice_total(items, Decimal(str(payload.get("discount", "0"))))
    invoice = invoice_repository.save_invoice(customer_id=str(payload["customer_id"]), total=total)
    return {"id": invoice["id"], "total": str(invoice["total"])}
