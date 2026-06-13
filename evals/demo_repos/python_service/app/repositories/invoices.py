from decimal import Decimal


class InvoiceRepository:
    def __init__(self) -> None:
        self.invoices: dict[str, dict[str, Decimal | str]] = {}

    def save_invoice(self, customer_id: str, total: Decimal) -> dict[str, Decimal | str]:
        invoice_id = f"inv-{len(self.invoices) + 1}"
        invoice = {"id": invoice_id, "customer_id": customer_id, "total": total}
        self.invoices[invoice_id] = invoice
        return invoice
