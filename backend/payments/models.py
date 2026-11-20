from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.models import Tenant
from businesses.models import Business
from customers.models import Customer


class Payment(models.Model):
    PAYMENT_METHOD_BANK_TRANSFER = 'bank_transfer'
    PAYMENT_METHOD_CARD = 'card'
    PAYMENT_METHOD_CASH = 'cash'
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_BANK_TRANSFER, 'Bank transfer'),
        (PAYMENT_METHOD_CARD, 'Card'),
        (PAYMENT_METHOD_CASH, 'Cash'),
    ]

    tenant = models.ForeignKey(Tenant, related_name='payments', on_delete=models.CASCADE)
    business = models.ForeignKey(Business, related_name='payments', on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name='payments', on_delete=models.CASCADE)
    invoice = models.ForeignKey('documents.Document', related_name='payments', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_METHOD_BANK_TRANSFER)
    reference = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-payment_date']

    def clean(self):
        super().clean()
        if self.tenant_id and self.business_id and self.business.tenant_id != self.tenant_id:
            raise ValidationError({'business': 'Business must belong to the same tenant as the payment.'})
        if self.tenant_id and self.customer_id and self.customer.tenant_id != self.tenant_id:
            raise ValidationError({'customer': 'Customer must belong to the same tenant as the payment.'})
        if self.business_id and self.customer_id and self.customer.business_id != self.business_id:
            raise ValidationError({'customer': 'Customer must belong to the same business as the payment.'})
        if self.invoice_id and self.tenant_id and self.invoice.tenant_id != self.tenant_id:
            raise ValidationError({'invoice': 'Invoice must belong to the same tenant as the payment.'})
        if self.invoice_id and self.business_id and self.invoice.business_id != self.business_id:
            raise ValidationError({'invoice': 'Invoice must belong to the same business as the payment.'})
        if self.invoice_id and self.customer_id and self.invoice.customer_id != self.customer_id:
            raise ValidationError({'invoice': 'Invoice customer must match the payment customer.'})
        if self.amount <= Decimal('0.00'):
            raise ValidationError({'amount': 'Payment amount must be greater than zero.'})

    def __str__(self):
        return f'{self.amount} for {self.customer.name}'
