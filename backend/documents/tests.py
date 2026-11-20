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


    def test_invoice_numbering_uses_invoice_sequence(self):
        response = self.client.post('/api/v1/documents/', {
            'business': self.business.id,
            'customer': self.customer.id,
            'document_type': 'INVOICE',
            'status': 'issued',
            'issue_date': '2026-11-20',
            'line_items': [{
                'description': 'Maintenance service',
                'quantity': '1.00',
                'unit_of_measure': 'job',
                'unit_price': '1000.00',
                'discount': '0.00',
                'tax_rate': '0.00',
            }],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['document_number'], 'MEGG-INV-0001')

    def test_multiple_tenant_memberships_require_explicit_selection_for_writes(self):
        second_tenant = Tenant.objects.create(name='Second Tenant', slug='second-tenant')
        TenantMembership.objects.create(user=self.user, tenant=second_tenant, role=TenantMembership.ROLE_MANAGER)

        payload = {
            'business': self.business.id,
            'customer': self.customer.id,
            'document_type': 'QUOTATION',
            'status': 'draft',
            'issue_date': '2026-11-20',
            'line_items': [{
                'description': 'Design work',
                'quantity': '1.00',
                'unit_price': '500.00',
                'discount': '0.00',
                'tax_rate': '0.00',
            }],
        }
        ambiguous = self.client.post('/api/v1/documents/', payload, format='json')
        self.assertEqual(ambiguous.status_code, status.HTTP_403_FORBIDDEN)

        selected = self.client.post(
            '/api/v1/documents/',
            payload,
            format='json',
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )
        self.assertEqual(selected.status_code, status.HTTP_201_CREATED, selected.data)


    def test_quotation_status_must_follow_valid_lifecycle(self):
        create_response = self.client.post('/api/v1/documents/', {
            'business': self.business.id,
            'customer': self.customer.id,
            'document_type': 'QUOTATION',
            'status': 'draft',
            'issue_date': '2026-11-20',
            'line_items': [{
                'description': 'Web development',
                'quantity': '1.00',
                'unit_price': '5000.00',
                'discount': '0.00',
                'tax_rate': '0.00',
            }],
        }, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED, create_response.data)
        document_id = create_response.data['id']

        invalid = self.client.patch(f'/api/v1/documents/{document_id}/', {'status': 'paid'}, format='json')
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

        issued = self.client.patch(f'/api/v1/documents/{document_id}/', {'status': 'issued'}, format='json')
        self.assertEqual(issued.status_code, status.HTTP_200_OK, issued.data)

        invalid_after_issue = self.client.patch(f'/api/v1/documents/{document_id}/', {'status': 'paid'}, format='json')
        self.assertEqual(invalid_after_issue.status_code, status.HTTP_400_BAD_REQUEST)

    def test_viewer_membership_cannot_create_financial_documents(self):
        viewer = get_user_model().objects.create_user(username='viewer-user', password='StrongPass123!')
        TenantMembership.objects.create(user=viewer, tenant=self.tenant, role=TenantMembership.ROLE_VIEWER)
        viewer_client = APIClient()
        viewer_client.force_authenticate(user=viewer)
        response = viewer_client.post('/api/v1/documents/', {
            'business': self.business.id,
            'customer': self.customer.id,
            'document_type': 'QUOTATION',
            'status': 'draft',
            'line_items': [{
                'description': 'Read-only test',
                'quantity': '1.00',
                'unit_price': '100.00',
                'tax_rate': '0.00',
            }],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_issued_document_snapshot_preserves_business_and_customer_facts(self):
        response = self.client.post('/api/v1/documents/', {
            'business': self.business.id,
            'customer': self.customer.id,
            'document_type': 'INVOICE',
            'status': 'issued',
            'issue_date': '2026-11-20',
            'line_items': [{
                'description': 'Original maintenance work',
                'quantity': '1.00',
                'unit_price': '1250.00',
                'discount': '0.00',
                'tax_rate': '0.00',
            }],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        from documents.models import Document
        document = Document.objects.get(pk=response.data['id'])
        original_snapshot = document.issued_snapshot
        self.assertEqual(original_snapshot['business']['account_number'], '')
        self.assertEqual(original_snapshot['customer']['name'], 'Apex Logistics')
        self.assertEqual(original_snapshot['line_items'][0]['description'], 'Original maintenance work')
        self.assertIsNotNone(document.issued_snapshot_at)

        self.business.account_number = '1234567890'
        self.business.banking_institution = 'Changed Bank'
        self.business.save()
        self.customer.name = 'Renamed Customer'
        self.customer.save()
        document.refresh_from_db()
        self.assertEqual(document.issued_snapshot, original_snapshot)
        self.assertEqual(document.issued_snapshot['business']['account_number'], '')
        self.assertEqual(document.issued_snapshot['customer']['name'], 'Apex Logistics')

    def test_issued_document_has_downloadable_pdf_endpoint(self):
        response = self.client.post('/api/v1/documents/', {
            'business': self.business.id,
            'customer': self.customer.id,
            'document_type': 'INVOICE',
            'status': 'issued',
            'issue_date': '2026-11-20',
            'line_items': [{
                'description': 'PDF test service',
                'quantity': '1.00',
                'unit_price': '750.00',
                'discount': '0.00',
                'tax_rate': '0.00',
            }],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        pdf_response = self.client.get(f"/api/v1/documents/{response.data['id']}/pdf/")
        self.assertEqual(pdf_response.status_code, status.HTTP_200_OK)
        self.assertEqual(pdf_response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', pdf_response['Content-Disposition'])
        self.assertTrue(pdf_response.content.startswith(b'%PDF-'))

    def test_design_profile_rejects_unapproved_css_tokens(self):
        response = self.client.post('/api/v1/documents/design-profiles/', {
            'business': self.business.id,
            'document_type': 'INVOICE',
            'theme': 'MODERN',
            'design_tokens': {'custom_css': 'body { display: none; }'},
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_persisted_issued_snapshot_cannot_be_replaced(self):
        response = self.client.post('/api/v1/documents/', {
            'business': self.business.id,
            'customer': self.customer.id,
            'document_type': 'INVOICE',
            'status': 'issued',
            'issue_date': '2026-11-20',
            'line_items': [{
                'description': 'Immutable record test',
                'quantity': '1.00',
                'unit_price': '500.00',
                'discount': '0.00',
                'tax_rate': '0.00',
            }],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        from django.core.exceptions import ValidationError
        from documents.models import Document
        document = Document.objects.get(pk=response.data['id'])
        document.issued_snapshot = {'tampered': True}
        with self.assertRaises(ValidationError):
            document.save()

    def test_selected_theme_is_captured_in_issued_snapshot(self):
        from documents.models import Document, DocumentDesignProfile
        DocumentDesignProfile.objects.create(
            business=self.business,
            document_type='QUOTATION',
            theme='INDUSTRIAL',
            primary_colour='#334155',
        )
        response = self.client.post('/api/v1/documents/', {
            'business': self.business.id,
            'customer': self.customer.id,
            'document_type': 'QUOTATION',
            'status': 'issued',
            'issue_date': '2026-11-20',
            'line_items': [{
                'description': 'Theme snapshot test',
                'quantity': '1.00',
                'unit_price': '800.00',
                'discount': '0.00',
                'tax_rate': '0.00',
            }],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        document = Document.objects.get(pk=response.data['id'])
        self.assertEqual(document.issued_snapshot['presentation']['theme'], 'INDUSTRIAL')
        self.assertEqual(document.issued_snapshot['presentation']['primary_colour'], '#334155')
