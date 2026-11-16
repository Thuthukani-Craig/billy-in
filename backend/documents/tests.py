from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Tenant, TenantMembership
from businesses.models import Business
from customers.models import Customer


class QuotationWorkflowAPITest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='megg-user', password='StrongPass123!')
        self.tenant = Tenant.objects.create(name='MEGG Tenant', slug='megg-tenant')
        TenantMembership.objects.create(user=self.user, tenant=self.tenant, role=TenantMembership.ROLE_OWNER)
        self.business = Business.objects.create(
            tenant=self.tenant,
            name='MEGG Maintenance',
            trading_name='MEGG Maintenance',
            email='admin@megg.co.za',
            telephone='+27 21 345 2100',
            is_active=True,
        )
        self.customer = Customer.objects.create(
            tenant=self.tenant,
            business=self.business,
            name='Apex Logistics',
            customer_type='COMPANY',
            email='accounts@apex.co.za',
            telephone='+27 82 100 2001',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_quotation_with_line_items_and_business_numbering(self):
        payload = {
            'business': self.business.id,
            'customer': self.customer.id,
            'document_type': 'QUOTATION',
            'status': 'draft',
            'issue_date': '2026-11-12',
            'due_date': '2026-11-30',
            'notes': 'Scope of work and exclusions',
            'line_items': [
                {
                    'description': 'Electrical repair labour',
                    'quantity': '4.00',
                    'unit_of_measure': 'hours',
                    'unit_price': '450.00',
                    'discount': '0.00',
                    'tax_rate': '15.00',
                },
                {
                    'description': 'Materials',
                    'quantity': '1.00',
                    'unit_of_measure': 'job',
                    'unit_price': '1500.00',
                    'discount': '100.00',
                    'tax_rate': '15.00',
                },
            ],
        }

        response = self.client.post('/api/v1/documents/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        document = response.data
        self.assertEqual(document['document_type'], 'QUOTATION')
        self.assertTrue(document['document_number'].startswith('MEGG-'))
        self.assertIn('-QUO-', document['document_number'])
        self.assertEqual(document['subtotal'], '3300.00')
        self.assertEqual(document['discount_amount'], '100.00')
        self.assertEqual(document['tax_amount'], '480.00')
        self.assertEqual(document['total'], '3680.00')

    def test_create_non_vat_quotation_without_tax(self):
        payload = {
            'business': self.business.id,
            'customer': self.customer.id,
            'document_type': 'QUOTATION',
            'status': 'draft',
            'issue_date': '2026-11-12',
            'due_date': '2026-11-30',
            'notes': 'No VAT on this quotation',
            'line_items': [
                {
                    'description': 'Labour only',
                    'quantity': '2.00',
                    'unit_of_measure': 'hours',
                    'unit_price': '250.00',
                    'discount': '25.00',
                    'tax_rate': '0.00',
                },
            ],
        }

        response = self.client.post('/api/v1/documents/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['subtotal'], '500.00')
        self.assertEqual(response.data['discount_amount'], '25.00')
        self.assertEqual(response.data['tax_amount'], '0.00')
        self.assertEqual(response.data['total'], '475.00')

    def test_user_without_membership_cannot_access_other_tenant_businesses(self):
        other_tenant = Tenant.objects.create(name='Other Tenant', slug='other-tenant')
        other_business = Business.objects.create(tenant=other_tenant, name='Other Business', email='info@other.co.za')

        response = self.client.get(f'/api/v1/businesses/{other_business.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_business_specific_numbering_is_unique_across_same_tenant_businesses(self):
        second_business = Business.objects.create(
            tenant=self.tenant,
            name='Demo Retail Business',
            trading_name='Demo Retail',
            email='sales@demo-retail.co.za',
            telephone='+27 11 222 3333',
            is_active=True,
        )
        second_customer = Customer.objects.create(
            tenant=self.tenant,
            business=second_business,
            name='Retail Group',
            customer_type='COMPANY',
            email='orders@retailgroup.co.za',
            telephone='+27 82 444 5555',
        )

        first_response = self.client.post('/api/v1/documents/', {
            'business': self.business.id,
            'customer': self.customer.id,
            'document_type': 'QUOTATION',
            'status': 'draft',
            'issue_date': '2026-11-12',
            'line_items': [{
                'description': 'Maintenance task',
                'quantity': '1.00',
                'unit_of_measure': 'job',
                'unit_price': '1000.00',
                'discount': '0.00',
                'tax_rate': '15.00',
            }],
        }, format='json')
        second_response = self.client.post('/api/v1/documents/', {
            'business': second_business.id,
            'customer': second_customer.id,
            'document_type': 'QUOTATION',
            'status': 'draft',
            'issue_date': '2026-11-12',
            'line_items': [{
                'description': 'Retail product supply',
                'quantity': '1.00',
                'unit_of_measure': 'job',
                'unit_price': '2000.00',
                'discount': '0.00',
                'tax_rate': '15.00',
            }],
        }, format='json')

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(first_response.data['document_number'].startswith('MEGG-QUO-'))
        self.assertTrue(second_response.data['document_number'].startswith('DEMO-QUO-'))
        self.assertNotEqual(first_response.data['document_number'], second_response.data['document_number'])

    def test_other_tenant_document_access_is_filtered_out(self):
        other_tenant = Tenant.objects.create(name='External Tenant', slug='external-tenant')
        other_business = Business.objects.create(tenant=other_tenant, name='External Business', email='info@external.co.za')
        other_customer = Customer.objects.create(
            tenant=other_tenant,
            business=other_business,
            name='Outside Client',
            customer_type='COMPANY',
            email='contact@outside.co.za',
        )

        self.client.post('/api/v1/documents/', {
            'business': other_business.id,
            'customer': other_customer.id,
            'document_type': 'QUOTATION',
            'status': 'draft',
            'issue_date': '2026-11-12',
            'line_items': [{
                'description': 'Outside work',
                'quantity': '1.00',
                'unit_of_measure': 'job',
                'unit_price': '2500.00',
                'discount': '0.00',
                'tax_rate': '15.00',
            }],
        }, format='json')

        response = self.client.get('/api/v1/documents/', {'business_id': other_business.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
