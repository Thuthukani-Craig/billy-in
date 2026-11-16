import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'billyin.settings')
os.environ['DATABASE_NAME'] = 'billyin_browser.sqlite3'

import django

django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Tenant, TenantMembership
from businesses.models import Business
from customers.models import Customer

User = get_user_model()
User.objects.filter(username='qa-browser-user').delete()
for slug in ['megg-workspace', 'vala-workspace']:
    Tenant.objects.filter(slug=slug).delete()

user = User.objects.create_user(username='qa-browser-user', password='StrongPass123!')
megg_tenant = Tenant.objects.create(name='MEGG Workspace', slug='megg-workspace')
vala_tenant = Tenant.objects.create(name='Vala Workspace', slug='vala-workspace')
TenantMembership.objects.create(user=user, tenant=megg_tenant, role=TenantMembership.ROLE_OWNER, is_active=True)
TenantMembership.objects.create(user=user, tenant=vala_tenant, role=TenantMembership.ROLE_MANAGER, is_active=True)

Business.objects.create(
    tenant=megg_tenant,
    name='MEGG Maintenance',
    trading_name='MEGG Maintenance',
    email='admin@megg.example',
    telephone='+27 11 000 0000',
    physical_address='1 Service Road',
    primary_brand_colour='#2563EB',
    is_active=True,
)
Business.objects.create(
    tenant=megg_tenant,
    name='Demo Retail Business',
    trading_name='Demo Retail',
    email='hello@demo-retail.example',
    telephone='+27 11 111 1111',
    physical_address='2 Market Lane',
    primary_brand_colour='#10b981',
    is_active=True,
)
Business.objects.create(
    tenant=vala_tenant,
    name='Vala Technologies',
    trading_name='Vala Tech',
    email='hello@vala.example',
    telephone='+27 21 222 2222',
    physical_address='3 Digital Avenue',
    primary_brand_colour='#7c3aed',
    is_active=True,
)

megg = Business.objects.get(tenant=megg_tenant, name='MEGG Maintenance')
demo = Business.objects.get(tenant=megg_tenant, name='Demo Retail Business')
vala = Business.objects.get(tenant=vala_tenant, name='Vala Technologies')

Customer.objects.filter(business__in=[megg, demo, vala]).delete()
Customer.objects.create(
    tenant=megg_tenant,
    business=megg,
    name='Apex Repair Group',
    customer_type='COMPANY',
    email='ops@apex.example',
    telephone='+27 82 100 2001',
    physical_address='12 Fix Avenue',
    is_active=True,
)
Customer.objects.create(
    tenant=megg_tenant,
    business=demo,
    name='Demo Market Clients',
    customer_type='COMPANY',
    email='accounts@market.example',
    telephone='+27 82 222 2222',
    physical_address='44 Retail Road',
    is_active=True,
)
Customer.objects.create(
    tenant=vala_tenant,
    business=vala,
    name='Ndlovu Digital',
    customer_type='COMPANY',
    email='hello@ndlovu.example',
    telephone='+27 82 333 3333',
    physical_address='9 Dev Place',
    is_active=True,
)

print('sandbox data seeded')
