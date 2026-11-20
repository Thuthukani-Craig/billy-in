from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from accounts.tenant_context import resolve_request_tenant
from accounts.permissions import TenantWorkspacePermission
from .models import Document, DocumentDesignProfile
from .serializers import DocumentSerializer, DocumentDesignProfileSerializer
from .rendering import render_document_pdf


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related('tenant', 'business', 'customer', 'payment').prefetch_related('line_items').all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, TenantWorkspacePermission]

    def get_queryset(self):
        queryset = Document.objects.select_related('tenant', 'business', 'customer', 'payment').prefetch_related('line_items').all()
        if not self.request.user.is_superuser:
            tenant = resolve_request_tenant(self.request)
            queryset = queryset.filter(tenant_id=tenant.id)
        business_id = self.request.query_params.get('business_id')
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        document_type = self.request.query_params.get('document_type')
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        return queryset

    @action(detail=True, methods=['get'], url_path='pdf')
    def pdf(self, request, pk=None):
        document = self.get_object()
        if not document.issued_snapshot:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Only issued documents with a preserved snapshot can be downloaded as PDF.')
        pdf_bytes = render_document_pdf(document)
        filename = f"{document.document_number}.pdf".replace('"', '').replace('\\\\', '')
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = str(len(pdf_bytes))
        return response



class DocumentDesignProfileViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentDesignProfileSerializer
    permission_classes = [IsAuthenticated, TenantWorkspacePermission]

    def get_queryset(self):
        queryset = DocumentDesignProfile.objects.select_related("business")
        if not self.request.user.is_superuser:
            tenant = resolve_request_tenant(self.request)
            queryset = queryset.filter(business__tenant_id=tenant.id)
        business_id = self.request.query_params.get("business_id")
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        return queryset
