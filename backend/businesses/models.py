from decimal import Decimal

from django.db import models
from django.utils import timezone

from accounts.models import Tenant


class Business(models.Model):
    tenant = models.ForeignKey(Tenant, related_name='businesses', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    trading_name = models.CharField(max_length=255, blank=True)
    registration_number = models.CharField(max_length=128, blank=True)
    vat_registration_number = models.CharField(max_length=128, blank=True)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    physical_address = models.TextField(blank=True)
    postal_address = models.TextField(blank=True)
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    primary_brand_colour = models.CharField(max_length=20, default='#2563EB')
    banking_institution = models.CharField(max_length=255, blank=True)
    account_holder = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=64, blank=True)
    branch_code = models.CharField(max_length=32, blank=True)
    account_type = models.CharField(max_length=128, blank=True)
    payment_instructions = models.TextField(blank=True)
    default_payment_terms = models.CharField(max_length=120, blank=True)
    invoice_footer = models.TextField(blank=True)
    next_quotation_number = models.PositiveIntegerField(default=1)
    next_invoice_number = models.PositiveIntegerField(default=1)
    next_receipt_number = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'name'], name='unique_business_name_per_tenant'),
        ]

    def __str__(self):
        return self.name

    @property
    def business_code(self):
        code = ''.join(ch for ch in self.name.upper() if ch.isalnum())[:4]
        return code or 'BIZ'

    def get_next_document_number(self, document_type):
        code_map = {
            'QUOTATION': ('QUO', 'next_quotation_number'),
            'INVOICE': ('INV', 'next_invoice_number'),
            'RECEIPT': ('REC', 'next_receipt_number'),
        }
        prefix, field_name = code_map[document_type]
        current_number = getattr(self, field_name)
        sequence_number = current_number
        setattr(self, field_name, current_number + 1)
        self.save(update_fields=[field_name])
        return f'{self.business_code}-{prefix}-{sequence_number:04d}'

    @property
    def total_business_amount(self):
        from documents.models import Document

        total = Decimal('0.00')
        for document in self.documents.filter(document_type='INVOICE'):
            total += document.total
        return total
