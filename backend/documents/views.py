from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import TenantMembership
from .models import Document
from .serializers import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related('tenant', 'business', 'customer', 'payment').prefetch_related('line_items').all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Document.objects.select_related('tenant', 'business', 'customer', 'payment').prefetch_related('line_items').all()
        if not self.request.user.is_superuser:
            tenant_ids = TenantMembership.objects.filter(user=self.request.user, is_active=True).values_list('tenant_id', flat=True)
            queryset = queryset.filter(tenant_id__in=tenant_ids)
        business_id = self.request.query_params.get('business_id')
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        document_type = self.request.query_params.get('document_type')
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        return queryset
