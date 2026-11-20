from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from accounts.tenant_context import resolve_request_tenant
from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related('tenant', 'business', 'customer', 'invoice').all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Payments cannot be deleted. A controlled reversal workflow will be provided.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def get_queryset(self):
        queryset = Payment.objects.select_related('tenant', 'business', 'customer', 'invoice').all()
        if not self.request.user.is_superuser:
            tenant_ids = TenantMembership.objects.filter(user=self.request.user, is_active=True).values_list('tenant_id', flat=True)
            queryset = queryset.filter(tenant_id__in=tenant_ids)
        business_id = self.request.query_params.get('business_id')
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        return queryset
