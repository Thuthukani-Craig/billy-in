from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import TenantMembership
from .models import Business
from .serializers import BusinessSerializer


class BusinessViewSet(viewsets.ModelViewSet):
    queryset = Business.objects.select_related('tenant').all()
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Business.objects.select_related('tenant').all()
        if not self.request.user.is_superuser:
            tenant_ids = TenantMembership.objects.filter(user=self.request.user, is_active=True).values_list('tenant_id', flat=True)
            queryset = queryset.filter(tenant_id__in=tenant_ids)
        active = self.request.query_params.get('active')
        if active is not None:
            queryset = queryset.filter(is_active=active.lower() == 'true')
        return queryset
