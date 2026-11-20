from decimal import Decimal
from pathlib import PurePosixPath
from uuid import uuid4

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone


def _money(value):
    return format(Decimal(value or 0).quantize(Decimal("0.01")), "f")


def build_issued_snapshot(document):
    """Build a self-contained record of the facts shown when a document is issued."""
    business = document.business
    customer = document.customer
    logo_name = ""
    if business.logo:
        try:
            business.logo.open("rb")
            try:
                logo_bytes = business.logo.read()
            finally:
                business.logo.close()
            original_name = PurePosixPath(business.logo.name).name
            immutable_name = f"document_snapshots/{document.tenant_id}/{document.pk}/{uuid4().hex}_{original_name}"
            logo_name = default_storage.save(immutable_name, ContentFile(logo_bytes))
        except (ValueError, OSError):
            logo_name = ""

    from .models import DocumentDesignProfile
    profile = DocumentDesignProfile.objects.filter(business=business, document_type=document.document_type).first()
    presentation = {
        "theme": profile.theme if profile else "CLASSIC",
        "primary_colour": (profile.primary_colour if profile else business.primary_brand_colour) or "",
        "show_logo": profile.show_logo if profile else True,
        "show_payment_details": profile.show_payment_details if profile else True,
        "show_business_registration": profile.show_business_registration if profile else True,
        "show_customer_vat_number": profile.show_customer_vat_number if profile else True,
        "design_tokens": profile.design_tokens if profile else {},
    }

    return {
        "schema_version": 1,
        "document": {
            "id": document.pk,
            "type": document.document_type,
            "number": document.document_number,
            "status_at_issue": document.status,
            "issue_date": document.issue_date.isoformat() if document.issue_date else None,
            "due_date": document.due_date.isoformat() if document.due_date else None,
            "notes": document.notes,
        },
        "business": {
            "name": business.name,
            "trading_name": business.trading_name,
            "registration_number": business.registration_number,
            "vat_registration_number": business.vat_registration_number,
            "email": business.email,
            "telephone": business.telephone,
            "physical_address": business.physical_address,
            "postal_address": business.postal_address,
            "logo_storage_name": logo_name,
            "primary_brand_colour": business.primary_brand_colour,
            "banking_institution": business.banking_institution,
            "account_holder": business.account_holder,
            "account_number": business.account_number,
            "branch_code": business.branch_code,
            "account_type": business.account_type,
            "payment_instructions": business.payment_instructions,
            "default_payment_terms": business.default_payment_terms,
            "invoice_footer": business.invoice_footer,
        },
        "customer": {
            "type": customer.customer_type,
            "name": customer.name,
            "contact_person": customer.contact_person,
            "email": customer.email,
            "telephone": customer.telephone,
            "alternative_telephone": customer.alternative_telephone,
            "physical_address": customer.physical_address,
            "billing_address": customer.billing_address,
            "vat_number": customer.vat_number,
        },
        "line_items": [
            {
                "description": item.description,
                "quantity": _money(item.quantity),
                "unit_of_measure": item.unit_of_measure,
                "unit_price": _money(item.unit_price),
                "discount": _money(item.discount),
                "tax_rate": _money(item.tax_rate),
                "line_subtotal": _money(item.line_subtotal),
                "line_tax": _money(item.line_tax),
                "line_total": _money(item.line_total),
            }
            for item in document.line_items.all()
        ],
        "totals": {
            "subtotal": _money(document.subtotal),
            "discount_amount": _money(document.discount_amount),
            "tax_amount": _money(document.tax_amount),
            "total": _money(document.total),
            "amount_paid": _money(document.amount_paid),
            "outstanding_balance": _money(document.outstanding_balance),
        },
        "presentation": presentation,
        "captured_at": timezone.now().isoformat(),
    }


def capture_issued_snapshot(document):
    """Capture once; later edits to profiles, customers or templates cannot rewrite it."""
    if document.issued_snapshot:
        return document.issued_snapshot
    snapshot = build_issued_snapshot(document)
    document.issued_snapshot = snapshot
    document.issued_snapshot_at = timezone.now()
    document.save(update_fields=["issued_snapshot", "issued_snapshot_at", "updated_at"])
    return snapshot
