from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.database import get_db

router = APIRouter(prefix="/invoices", tags=["invoices"])


class InvoiceItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class InvoiceCreate(BaseModel):
    invoice_no: Optional[str] = None
    issue_date: date
    due_date: date
    client_id: int
    address: Optional[str] = None
    items: List[InvoiceItemCreate]
    tax: float = Field(default=0.0, ge=0)


class ClientResponse(BaseModel):
    id: int
    name: str
    address: str
    company_registration_no: str


class InvoiceItemResponse(BaseModel):
    product_id: int
    name: str
    unit_price: float
    quantity: int
    line_total: float


class InvoiceResponse(BaseModel):
    id: int
    invoice_no: str
    issue_date: date
    due_date: date
    client: ClientResponse
    address: str
    items: List[InvoiceItemResponse]
    tax: float
    total: float


def _fetch_client(cursor, client_id: int):
    cursor.execute(
        "SELECT id, name, address, company_registration_no FROM clients WHERE id = ?",
        (client_id,),
    )
    return cursor.fetchone()


def _generate_invoice_no(cursor) -> str:
    cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM invoices")
    next_id = cursor.fetchone()["next_id"]
    return f"INV-{next_id:05d}"


@router.post("", status_code=201, response_model=InvoiceResponse)
def create_invoice(payload: InvoiceCreate):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Invoice must include at least one item")

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            client_row = _fetch_client(cursor, payload.client_id)
            if client_row is None:
                raise HTTPException(status_code=404, detail="Client not found")

            invoice_no = payload.invoice_no
            if invoice_no:
                cursor.execute("SELECT 1 FROM invoices WHERE invoice_no = ?", (invoice_no,))
                if cursor.fetchone():
                    raise HTTPException(status_code=409, detail="Invoice number already exists")
            else:
                invoice_no = _generate_invoice_no(cursor)

            address = payload.address or client_row["address"]

            item_rows = []
            total = 0.0
            for item in payload.items:
                cursor.execute("SELECT id, name, price FROM products WHERE id = ?", (item.product_id,))
                product = cursor.fetchone()
                if product is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Product not found: {item.product_id}",
                    )
                line_total = float(product["price"]) * item.quantity
                total += line_total
                item_rows.append(
                    {
                        "product_id": product["id"],
                        "name": product["name"],
                        "unit_price": float(product["price"]),
                        "quantity": item.quantity,
                        "line_total": line_total,
                    }
                )

            total_with_tax = total + float(payload.tax)

            cursor.execute(
                """
                INSERT INTO invoices (
                    invoice_no,
                    issue_date,
                    due_date,
                    client_id,
                    address,
                    tax,
                    total
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_no,
                    payload.issue_date.isoformat(),
                    payload.due_date.isoformat(),
                    payload.client_id,
                    address,
                    float(payload.tax),
                    total_with_tax,
                ),
            )
            invoice_id = cursor.lastrowid

            for item in item_rows:
                cursor.execute(
                    """
                    INSERT INTO invoice_items (
                        invoice_id,
                        product_id,
                        quantity,
                        unit_price,
                        line_total
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        invoice_id,
                        item["product_id"],
                        item["quantity"],
                        item["unit_price"],
                        item["line_total"],
                    ),
                )

            return InvoiceResponse(
                id=invoice_id,
                invoice_no=invoice_no,
                issue_date=payload.issue_date,
                due_date=payload.due_date,
                client=ClientResponse(
                    id=client_row["id"],
                    name=client_row["name"],
                    address=client_row["address"],
                    company_registration_no=client_row["company_registration_no"],
                ),
                address=address,
                items=[InvoiceItemResponse(**item) for item in item_rows],
                tax=float(payload.tax),
                total=total_with_tax,
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")


@router.get("", response_model=dict)
def list_invoices():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT invoices.id,
                       invoices.invoice_no,
                       invoices.issue_date,
                       invoices.due_date,
                       invoices.total,
                       clients.name AS client_name
                FROM invoices
                JOIN clients ON clients.id = invoices.client_id
                ORDER BY invoices.id
                """
            )
            rows = cursor.fetchall()
            invoices = [
                {
                    "id": row["id"],
                    "invoice_no": row["invoice_no"],
                    "issue_date": row["issue_date"],
                    "due_date": row["due_date"],
                    "client_name": row["client_name"],
                    "total": row["total"],
                }
                for row in rows
            ]
            return {"invoices": invoices}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT invoices.id,
                       invoices.invoice_no,
                       invoices.issue_date,
                       invoices.due_date,
                       invoices.address,
                       invoices.tax,
                       invoices.total,
                       clients.id AS client_id,
                       clients.name,
                       clients.address AS client_address,
                       clients.company_registration_no
                FROM invoices
                JOIN clients ON clients.id = invoices.client_id
                WHERE invoices.id = ?
                """,
                (invoice_id,),
            )
            invoice_row = cursor.fetchone()
            if invoice_row is None:
                raise HTTPException(status_code=404, detail="Invoice not found")

            cursor.execute(
                """
                SELECT invoice_items.product_id,
                       products.name,
                       invoice_items.unit_price,
                       invoice_items.quantity,
                       invoice_items.line_total
                FROM invoice_items
                JOIN products ON products.id = invoice_items.product_id
                WHERE invoice_items.invoice_id = ?
                ORDER BY invoice_items.id
                """,
                (invoice_id,),
            )
            item_rows = cursor.fetchall()
            items = [
                {
                    "product_id": row["product_id"],
                    "name": row["name"],
                    "unit_price": float(row["unit_price"]),
                    "quantity": row["quantity"],
                    "line_total": float(row["line_total"]),
                }
                for row in item_rows
            ]

            return InvoiceResponse(
                id=invoice_row["id"],
                invoice_no=invoice_row["invoice_no"],
                issue_date=date.fromisoformat(invoice_row["issue_date"]),
                due_date=date.fromisoformat(invoice_row["due_date"]),
                client=ClientResponse(
                    id=invoice_row["client_id"],
                    name=invoice_row["name"],
                    address=invoice_row["client_address"],
                    company_registration_no=invoice_row["company_registration_no"],
                ),
                address=invoice_row["address"],
                items=[InvoiceItemResponse(**item) for item in items],
                tax=float(invoice_row["tax"]),
                total=float(invoice_row["total"]),
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(invoice_id: int):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM invoices WHERE id = ?", (invoice_id,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Invoice not found")

            cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            return None
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")
