from decimal import Decimal

from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import TenantMembership
from businesses.models import Business
from customers.models import Customer
from documents.models import Document
from payments.models import Payment


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    # Begin with the authenticated user's tenant boundary before applying any
    # user-supplied filters. Never let business_id widen this queryset.
    if request.user.is_superuser:
        businesses = Business.objects.select_related('tenant').all()
        customers = Customer.objects.all()
        documents = Document.objects.select_related('customer').all()
        payments = Payment.objects.select_related('customer').all()
    else:
        tenant_ids = TenantMembership.objects.filter(
            user=request.user, is_active=True, tenant__is_active=True
        ).values_list('tenant_id', flat=True)
        businesses = Business.objects.select_related('tenant').filter(tenant_id__in=tenant_ids)
        customers = Customer.objects.filter(tenant_id__in=tenant_ids)
        documents = Document.objects.select_related('customer').filter(tenant_id__in=tenant_ids)
        payments = Payment.objects.select_related('customer').filter(tenant_id__in=tenant_ids)

    business_id = request.query_params.get('business_id')
    if business_id:
        businesses = businesses.filter(id=business_id)
        customers = customers.filter(business_id=business_id)
        documents = documents.filter(business_id=business_id)
        payments = payments.filter(business_id=business_id)

    total_invoiced = documents.filter(document_type='INVOICE').aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    total_payments = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    outstanding_balances = documents.filter(document_type='INVOICE').aggregate(total=Sum('outstanding_balance'))['total'] or Decimal('0.00')
    overdue_invoices = documents.filter(document_type='INVOICE', status='overdue').count()

    response = {
        'business_count': businesses.count(),
        'active_business_count': businesses.filter(is_active=True).count(),
        'customer_count': customers.count(),
        'total_invoiced': str(total_invoiced),
        'total_payments_received': str(total_payments),
        'outstanding_balances': str(outstanding_balances),
        'overdue_invoices': overdue_invoices,
    }

    response['recent_invoices'] = [
        {
            'id': document.id,
            'document_number': document.document_number,
            'customer_name': document.customer.name,
            'total': str(document.total),
            'status': document.status,
            'created_at': document.created_at.isoformat(),
        }
        for document in documents.filter(document_type='INVOICE').order_by('-created_at')[:5]
    ]
    response['recent_quotations'] = [
        {
            'id': document.id,
            'document_number': document.document_number,
            'customer_name': document.customer.name,
            'total': str(document.total),
            'status': document.status,
            'created_at': document.created_at.isoformat(),
        }
        for document in documents.filter(document_type='QUOTATION').order_by('-created_at')[:5]
    ]
    response['recent_payments'] = [
        {
            'id': payment.id,
            'customer_name': payment.customer.name,
            'amount': str(payment.amount),
            'payment_method': payment.payment_method,
            'payment_date': payment.payment_date.isoformat(),
        }
        for payment in payments.order_by('-payment_date')[:5]
    ]
    return Response(response)
