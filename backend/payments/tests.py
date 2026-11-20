from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Tenant, TenantMembership
from businesses.models import Business
from customers.models import Customer
from documents.models import Document, DocumentLineItem


class PaymentAllocationAPITest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='payment-user', password='StrongPass123!')
        self.tenant = Tenant.objects.create(name='Payment Tenant', slug='payment-tenant')
        TenantMembership.objects.create(user=self.user, tenant=self.tenant, role=TenantMembership.ROLE_OWNER)
        self.business = Business.objects.create(tenant=self.tenant, name='Payment Business')
        self.customer = Customer.objects.create(tenant=self.tenant, business=self.business, name='Customer One')
        self.invoice = Document.objects.create(
            tenant=self.tenant,
            business=self.business,
            customer=self.customer,
            document_type=Document.DOCUMENT_TYPE_INVOICE,
            document_number='PAY-INV-0001',
            status=Document.STATUS_ISSUED,
        )
        DocumentLineItem.objects.create(
            document=self.invoice,
            description='Consulting services',
            quantity=Decimal('1.00'),
            unit_price=Decimal('1000.00'),
            tax_rate=Decimal('0.00'),
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def payment_payload(self, amount):
        return {
            'business': self.business.id,
            'customer': self.customer.id,
            'invoice': self.invoice.id,
            'amount': str(amount),
            'payment_date': '2026-11-20',
            'payment_method': 'bank_transfer',
            'reference': 'BANK-REF-001',
        }

    def test_partial_payment_updates_invoice_balance(self):
        response = self.client.post('/api/v1/payments/', self.payment_payload('400.00'), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal('400.00'))
        self.assertEqual(self.invoice.outstanding_balance, Decimal('600.00'))
        self.assertEqual(self.invoice.status, Document.STATUS_PARTIALLY_PAID)

    def test_full_payment_marks_invoice_paid(self):
        response = self.client.post('/api/v1/payments/', self.payment_payload('1000.00'), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal('1000.00'))
        self.assertEqual(self.invoice.outstanding_balance, Decimal('0.00'))
        self.assertEqual(self.invoice.status, Document.STATUS_PAID)

    def test_overpayment_is_rejected_without_creating_payment(self):
        response = self.client.post('/api/v1/payments/', self.payment_payload('1000.01'), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.invoice.payments.count(), 0)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal('0.00'))

    def test_payment_cannot_be_allocated_to_another_customers_invoice(self):
        other_customer = Customer.objects.create(tenant=self.tenant, business=self.business, name='Other Customer')
        response = self.client.post('/api/v1/payments/', {
            **self.payment_payload('100.00'),
            'customer': other_customer.id,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.invoice.payments.count(), 0)

    def test_payment_records_cannot_be_deleted(self):
        response = self.client.post('/api/v1/payments/', self.payment_payload('100.00'), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        payment_id = response.data['id']
        delete_response = self.client.delete(f'/api/v1/payments/{payment_id}/')
        self.assertEqual(delete_response.status_code, 405)
        self.assertTrue(self.invoice.payments.filter(pk=payment_id).exists())


    def test_payment_can_generate_a_balanced_receipt_document(self):
        payment_response = self.client.post('/api/v1/payments/', self.payment_payload('250.00'), format='json')
        self.assertEqual(payment_response.status_code, 201, payment_response.data)

        receipt_response = self.client.post('/api/v1/documents/', {
            'business': self.business.id,
            'customer': self.customer.id,
            'document_type': 'RECEIPT',
            'payment': payment_response.data['id'],
            'issue_date': '2026-11-20',
        }, format='json')
        self.assertEqual(receipt_response.status_code, 201, receipt_response.data)
        self.assertEqual(receipt_response.data['document_number'], 'PAYM-REC-0001')
        self.assertEqual(receipt_response.data['total'], '250.00')
        self.assertEqual(receipt_response.data['amount_paid'], '250.00')
        self.assertEqual(receipt_response.data['outstanding_balance'], '0.00')
