from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.tenant_context import resolve_request_tenant
from accounts.permissions import TenantWorkspacePermission
from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.select_related('business', 'tenant').all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, TenantWorkspacePermission]

    def get_queryset(self):
        queryset = Customer.objects.select_related('business', 'tenant').all()
        if not self.request.user.is_superuser:
            tenant = resolve_request_tenant(self.request)
            queryset = queryset.filter(tenant_id=tenant.id)
        business_id = self.request.query_params.get('business_id')
        search = self.request.query_params.get('search')
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset
