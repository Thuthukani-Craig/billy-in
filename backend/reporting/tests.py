from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Tenant, TenantMembership
from businesses.models import Business


class DashboardTenantIsolationTest(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username='report-user', password='StrongPass123!')
        self.tenant = Tenant.objects.create(name='My Tenant', slug='my-tenant')
        TenantMembership.objects.create(user=user, tenant=self.tenant, role=TenantMembership.ROLE_OWNER)
        self.own_business = Business.objects.create(tenant=self.tenant, name='My Business')
        other_tenant = Tenant.objects.create(name='Other Tenant', slug='other-dashboard-tenant')
        self.other_business = Business.objects.create(tenant=other_tenant, name='Private Other Business')
        self.client = APIClient()
        self.client.force_authenticate(user=user)

    def test_business_filter_cannot_escape_membership_scope(self):
        response = self.client.get('/api/v1/reporting/dashboard/', {'business_id': self.other_business.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['business_count'], 0)
        self.assertEqual(response.data['active_business_count'], 0)

    def test_dashboard_without_filter_only_counts_accessible_tenant(self):
        response = self.client.get('/api/v1/reporting/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['business_count'], 1)
        self.assertEqual(response.data['active_business_count'], 1)
