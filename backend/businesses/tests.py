from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Tenant
from businesses.models import Business
from customers.models import Customer
from documents.models import Document, DocumentLineItem


class BusinessCustomerDocumentRelationshipTest(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Vala Tenant', slug='vala-tenant')
        self.business = Business.objects.create(
            tenant=self.tenant,
            name='Vala Technologies',
            email='hello@vala.co.za',
            is_active=True,
        )
        self.customer = Customer.objects.create(
            tenant=self.tenant,
            business=self.business,
            name='Ndlovu Projects',
            customer_type='COMPANY',
            email='info@ndlovu.co.za',
        )

    def test_customer_belongs_to_business(self):
        self.assertEqual(self.business.customers.count(), 1)
        self.assertEqual(self.business.customers.first(), self.customer)

    def test_document_business_customer_relationship_is_valid(self):
        document = Document.objects.create(
            tenant=self.tenant,
            business=self.business,
            customer=self.customer,
            document_type='INVOICE',
            document_number='VALA-INV-0001',
            status='issued',
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('15.00'),
            total=Decimal('115.00'),
        )
        self.assertEqual(document.customer.business, document.business)

        item = DocumentLineItem.objects.create(
            document=document,
            description='Development work',
            quantity=Decimal('2.00'),
            unit_price=Decimal('50.00'),
            discount=Decimal('0.00'),
            tax_rate=Decimal('15.00'),
        )

        self.assertEqual(item.line_subtotal, Decimal('100.00'))
        self.assertEqual(item.line_tax, Decimal('15.00'))
        self.assertEqual(item.line_total, Decimal('115.00'))

    def test_mismatched_business_customer_relationship_is_invalid(self):
        other_business = Business.objects.create(
            tenant=self.tenant,
            name='MEGG Maintenance',
            email='admin@megg.co.za',
        )
        other_customer = Customer.objects.create(
            tenant=self.tenant,
            business=other_business,
            name='Another Client',
            customer_type='COMPANY',
        )

        document = Document(
            tenant=self.tenant,
            business=self.business,
            customer=other_customer,
            document_type='INVOICE',
            document_number='VALA-INV-0002',
        )

        with self.assertRaises(ValidationError):
            document.full_clean()
