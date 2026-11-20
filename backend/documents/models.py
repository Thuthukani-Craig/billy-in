from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.models import Tenant
from businesses.models import Business
from customers.models import Customer


class Document(models.Model):
    DOCUMENT_TYPE_QUOTATION = 'QUOTATION'
    DOCUMENT_TYPE_INVOICE = 'INVOICE'
    DOCUMENT_TYPE_RECEIPT = 'RECEIPT'
    DOCUMENT_TYPE_CHOICES = [
        (DOCUMENT_TYPE_QUOTATION, 'Quotation'),
        (DOCUMENT_TYPE_INVOICE, 'Invoice'),
        (DOCUMENT_TYPE_RECEIPT, 'Receipt'),
    ]

    STATUS_DRAFT = 'draft'
    STATUS_ISSUED = 'issued'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_EXPIRED = 'expired'
    STATUS_PARTIALLY_PAID = 'partially_paid'
    STATUS_PAID = 'paid'
    STATUS_OVERDUE = 'overdue'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ISSUED, 'Issued'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_PARTIALLY_PAID, 'Partially Paid'),
        (STATUS_PAID, 'Paid'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    tenant = models.ForeignKey(Tenant, related_name='documents', on_delete=models.CASCADE)
    business = models.ForeignKey(Business, related_name='documents', on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name='documents', on_delete=models.CASCADE)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=50)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    issue_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    issued_snapshot = models.JSONField(default=dict, blank=True, editable=False)
    issued_snapshot_at = models.DateTimeField(null=True, blank=True, editable=False)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    outstanding_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    payment = models.OneToOneField('payments.Payment', null=True, blank=True, related_name='receipt_document', on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'document_number'], name='unique_document_number_per_tenant'),
        ]

    def __str__(self):
        return f'{self.document_number} ({self.document_type})'

    def clean(self):
        super().clean()
        if self.tenant_id and self.business_id and self.business.tenant_id != self.tenant_id:
            raise ValidationError({'business': 'Business must belong to the same tenant as the document.'})
        if self.customer_id and self.business_id and self.customer.business_id != self.business_id:
            raise ValidationError({'customer': 'Customer must belong to the selected business.'})
        if self.customer_id and self.tenant_id and self.customer.tenant_id != self.tenant_id:
            raise ValidationError({'customer': 'Customer must belong to the same tenant as the document.'})
        if self.document_type == self.DOCUMENT_TYPE_RECEIPT and self.payment is None:
            raise ValidationError({'payment': 'Receipts must be linked to a payment record.'})
        if self.payment_id and self.tenant_id and self.payment.tenant_id != self.tenant_id:
            raise ValidationError({'payment': 'Payment must belong to the same tenant as the receipt.'})
        if self.payment_id and self.business_id and self.payment.business_id != self.business_id:
            raise ValidationError({'payment': 'Payment must belong to the same business as the receipt.'})
        if self.payment_id and self.customer_id and self.payment.customer_id != self.customer_id:
            raise ValidationError({'payment': 'Payment customer must match the receipt customer.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        requested_update_fields = kwargs.pop('update_fields', None)
        if is_new:
            super().save(*args, **kwargs)

        self.subtotal = self.calculate_subtotal()
        self.discount_amount = self.calculate_discount_total()
        self.tax_amount = self.calculate_tax_total()
        self.total = self.calculate_total()
        self.outstanding_balance = self.total - self.amount_paid

        calculated_fields = {
            'subtotal', 'discount_amount', 'tax_amount', 'total',
            'outstanding_balance', 'updated_at',
        }
        if requested_update_fields is not None:
            calculated_fields.update(requested_update_fields)
        super().save(update_fields=list(calculated_fields))

    def calculate_subtotal(self):
        return sum((item.line_subtotal for item in self.line_items.all()), Decimal('0.00'))

    def calculate_discount_total(self):
        return sum((item.discount for item in self.line_items.all()), Decimal('0.00'))

    def calculate_tax_total(self):
        return sum((item.line_tax for item in self.line_items.all()), Decimal('0.00'))

    def calculate_total(self):
        return sum((item.line_total for item in self.line_items.all()), Decimal('0.00'))


class DocumentLineItem(models.Model):
    document = models.ForeignKey(Document, related_name='line_items', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('1.00'))
    unit_of_measure = models.CharField(max_length=32, blank=True)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    line_subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    line_tax = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.description

    def clean(self):
        super().clean()
        if self.quantity <= Decimal('0.00'):
            raise ValidationError({'quantity': 'Quantity must be greater than zero.'})
        if self.unit_price < Decimal('0.00'):
            raise ValidationError({'unit_price': 'Unit price cannot be negative.'})
        if self.discount < Decimal('0.00'):
            raise ValidationError({'discount': 'Discount cannot be negative.'})
        if self.discount > self.quantity * self.unit_price:
            raise ValidationError({'discount': 'Discount cannot exceed the line subtotal.'})
        if self.tax_rate < Decimal('0.00') or self.tax_rate > Decimal('100.00'):
            raise ValidationError({'tax_rate': 'Tax rate must be between 0 and 100.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        subtotal = self.quantity * self.unit_price
        discount_amount = self.discount
        taxable_value = subtotal - discount_amount
        tax_amount = taxable_value * (self.tax_rate / Decimal('100'))
        total = taxable_value + tax_amount
        self.line_subtotal = subtotal
        self.line_tax = tax_amount
        self.line_total = total
        super().save(*args, **kwargs)
        self.document.save()


class DocumentDesignProfile(models.Model):
    THEME_CLASSIC = "CLASSIC"
    THEME_MODERN = "MODERN"
    THEME_MINIMAL = "MINIMAL"
    THEME_CORPORATE = "CORPORATE"
    THEME_BOLD = "BOLD"
    THEME_INDUSTRIAL = "INDUSTRIAL"
    THEME_CHOICES = [
        (THEME_CLASSIC, "Classic"),
        (THEME_MODERN, "Modern"),
        (THEME_MINIMAL, "Minimal"),
        (THEME_CORPORATE, "Corporate"),
        (THEME_BOLD, "Bold"),
        (THEME_INDUSTRIAL, "Industrial"),
    ]

    business = models.ForeignKey(Business, related_name="document_design_profiles", on_delete=models.CASCADE)
    document_type = models.CharField(max_length=20, choices=Document.DOCUMENT_TYPE_CHOICES)
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default=THEME_CLASSIC)
    primary_colour = models.CharField(max_length=7, blank=True)
    show_logo = models.BooleanField(default=True)
    show_payment_details = models.BooleanField(default=True)
    show_business_registration = models.BooleanField(default=True)
    show_customer_vat_number = models.BooleanField(default=True)
    design_tokens = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["business", "document_type"], name="unique_business_document_design"),
        ]

    def clean(self):
        super().clean()
        if self.primary_colour and not (
            len(self.primary_colour) == 7 and self.primary_colour.startswith("#")
            and all(ch in "0123456789abcdefABCDEF" for ch in self.primary_colour[1:])
        ):
            raise ValidationError({"primary_colour": "Use a six-digit hexadecimal colour such as #2563EB."})
        allowed_tokens = {"accent_colour", "muted_colour", "font_scale", "corner_style"}
        if set(self.design_tokens) - allowed_tokens:
            raise ValidationError({"design_tokens": "Only approved design tokens may be configured."})
