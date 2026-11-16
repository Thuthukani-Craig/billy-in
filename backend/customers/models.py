from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.models import Tenant
from businesses.models import Business


class Customer(models.Model):
    CUSTOMER_TYPE_INDIVIDUAL = 'INDIVIDUAL'
    CUSTOMER_TYPE_COMPANY = 'COMPANY'
    CUSTOMER_TYPE_CHOICES = [
        (CUSTOMER_TYPE_INDIVIDUAL, 'Individual'),
        (CUSTOMER_TYPE_COMPANY, 'Company'),
    ]

    tenant = models.ForeignKey(Tenant, related_name='customers', on_delete=models.CASCADE)
    business = models.ForeignKey(Business, related_name='customers', on_delete=models.CASCADE)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES, default=CUSTOMER_TYPE_COMPANY)
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    alternative_telephone = models.CharField(max_length=50, blank=True)
    physical_address = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    vat_number = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'business', 'name'], name='unique_customer_per_tenant_business'),
        ]

    def clean(self):
        super().clean()
        if self.business_id and self.tenant_id and self.business.tenant_id != self.tenant_id:
            raise ValidationError({'business': 'Business must belong to the same tenant as the customer.'})

    def __str__(self):
        return f'{self.name} ({self.business.name})'
