from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import TenantMembership
from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.select_related('business', 'tenant').all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Customer.objects.select_related('business', 'tenant').all()
        if not self.request.user.is_superuser:
            tenant_ids = TenantMembership.objects.filter(user=self.request.user, is_active=True).values_list('tenant_id', flat=True)
            queryset = queryset.filter(tenant_id__in=tenant_ids)
        business_id = self.request.query_params.get('business_id')
        search = self.request.query_params.get('search')
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset
