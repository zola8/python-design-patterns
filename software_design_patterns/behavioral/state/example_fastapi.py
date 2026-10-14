from enum import Enum

import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel

app = FastAPI()


# ==========================================
# STATE MACHINE (Fixed type checker warning)
# ==========================================
class InvoiceStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


# Define transitions OUTSIDE the enum (fixes the type checker warning)
_TRANSITIONS = {
    InvoiceStatus.DRAFT: {InvoiceStatus.SENT, InvoiceStatus.CANCELLED},
    InvoiceStatus.SENT: {InvoiceStatus.PAID, InvoiceStatus.OVERDUE, InvoiceStatus.CANCELLED},
    InvoiceStatus.PAID: set(),  # Terminal
    InvoiceStatus.OVERDUE: {InvoiceStatus.PAID, InvoiceStatus.CANCELLED},
    InvoiceStatus.CANCELLED: set(),  # Terminal
}


class Invoice:
    def __init__(self, invoice_id: str, customer: str, amount: float):
        self.id = invoice_id
        self.customer = customer
        self.amount = amount
        self.status = InvoiceStatus.DRAFT

    def transition_to(self, new_status: InvoiceStatus):
        allowed = _TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(f"Invalid: {self.status.value} -> {new_status.value}")
        self.status = new_status

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer": self.customer,
            "amount": self.amount,
            "status": self.status.value,
            "allowed_transitions": [
                s.value for s in InvoiceStatus
                if s in _TRANSITIONS.get(self.status, set())
            ]
        }


# ==========================================
# IN-MEMORY STORE
# ==========================================
invoices: dict[str, Invoice] = {}
invoice_counter = 0


# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================
class CreateInvoiceRequest(BaseModel):
    customer: str
    amount: float


class TransitionRequest(BaseModel):
    new_status: str


# ==========================================
# ENDPOINTS
# ==========================================
@app.post("/invoices")
async def create_invoice(req: CreateInvoiceRequest):
    """Create a new invoice in DRAFT status."""
    global invoice_counter
    invoice_counter += 1
    invoice_id = f"INV-{invoice_counter:04d}"

    invoice = Invoice(
        invoice_id=invoice_id,
        customer=req.customer,
        amount=req.amount
    )
    invoices[invoice_id] = invoice

    return invoice.to_dict()


@app.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str):
    """Get invoice details and allowed transitions."""
    if invoice_id not in invoices:
        raise HTTPException(404, "Invoice not found")

    return invoices[invoice_id].to_dict()


@app.post("/invoices/{invoice_id}/transition")
async def transition_invoice(invoice_id: str, req: TransitionRequest):
    """Transition invoice to a new status."""
    if invoice_id not in invoices:
        raise HTTPException(404, "Invoice not found")

    invoice = invoices[invoice_id]

    try:
        new_status = InvoiceStatus(req.new_status)
    except ValueError:
        raise HTTPException(400, f"Unknown status: {req.new_status}")

    try:
        invoice.transition_to(new_status)
    except ValueError as e:
        raise HTTPException(409, str(e))  # 409 Conflict for invalid state transitions

    return invoice.to_dict()


@app.get("/invoices")
async def list_invoices():
    """List all invoices."""
    return [inv.to_dict() for inv in invoices.values()]


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
