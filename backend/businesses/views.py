from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.tenant_context import resolve_request_tenant
from accounts.permissions import TenantWorkspacePermission
from .models import Business
from .serializers import BusinessSerializer


class BusinessViewSet(viewsets.ModelViewSet):
    queryset = Business.objects.select_related('tenant').all()
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated, TenantWorkspacePermission]

    def get_queryset(self):
        queryset = Business.objects.select_related('tenant').all()
        if not self.request.user.is_superuser:
            tenant = resolve_request_tenant(self.request)
            queryset = queryset.filter(tenant_id=tenant.id)
        active = self.request.query_params.get('active')
        if active is not None:
            queryset = queryset.filter(is_active=active.lower() == 'true')
        return queryset
