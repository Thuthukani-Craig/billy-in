from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import F

from documents.models import Document
from .models import Payment


@transaction.atomic
def record_payment(*, tenant, business, customer, amount, invoice=None, **fields):
    """Persist a payment and allocate it to an invoice as one atomic operation."""
    amount = Decimal(amount)
    if amount <= Decimal("0.00"):
        raise DjangoValidationError({"amount": "Payment amount must be greater than zero."})

    locked_invoice = None
    if invoice is not None:
        locked_invoice = Document.objects.select_for_update().get(pk=invoice.pk)
        if locked_invoice.document_type != Document.DOCUMENT_TYPE_INVOICE:
            raise DjangoValidationError({"invoice": "Payments can only be allocated to invoices."})
        if locked_invoice.tenant_id != tenant.id or locked_invoice.business_id != business.id:
            raise DjangoValidationError({"invoice": "Invoice must belong to the selected tenant and business."})
        if locked_invoice.customer_id != customer.id:
            raise DjangoValidationError({"invoice": "Invoice customer must match the payment customer."})
        if locked_invoice.status == Document.STATUS_CANCELLED:
            raise DjangoValidationError({"invoice": "Cancelled invoices cannot receive payments."})
        if amount > locked_invoice.outstanding_balance:
            raise DjangoValidationError({"amount": "Payment exceeds the invoice's outstanding balance."})

    payment = Payment(
        tenant=tenant,
        business=business,
        customer=customer,
        invoice=locked_invoice,
        amount=amount,
        **fields,
    )
    payment.full_clean()
    payment.save()

    if locked_invoice is not None:
        locked_invoice.amount_paid = F("amount_paid") + amount
        locked_invoice.save(update_fields=["amount_paid", "updated_at"])
        locked_invoice.refresh_from_db(fields=["amount_paid", "total", "outstanding_balance", "status"])
        locked_invoice.outstanding_balance = locked_invoice.total - locked_invoice.amount_paid
        if locked_invoice.outstanding_balance == Decimal("0.00"):
            locked_invoice.status = Document.STATUS_PAID
        else:
            locked_invoice.status = Document.STATUS_PARTIALLY_PAID
        locked_invoice.save(update_fields=["outstanding_balance", "status", "updated_at"])

    return payment
