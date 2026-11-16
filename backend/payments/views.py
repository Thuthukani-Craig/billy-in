from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import TenantMembership
from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related('tenant', 'business', 'customer', 'invoice').all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Payment.objects.select_related('tenant', 'business', 'customer', 'invoice').all()
        if not self.request.user.is_superuser:
            tenant_ids = TenantMembership.objects.filter(user=self.request.user, is_active=True).values_list('tenant_id', flat=True)
            queryset = queryset.filter(tenant_id__in=tenant_ids)
        business_id = self.request.query_params.get('business_id')
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        return queryset
