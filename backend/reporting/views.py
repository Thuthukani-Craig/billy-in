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
    tenant_ids = TenantMembership.objects.filter(user=request.user, is_active=True).values_list('tenant_id', flat=True)
    if request.user.is_superuser:
        tenant_ids = None

    business_id = request.query_params.get('business_id')
    if business_id:
        businesses = Business.objects.filter(id=business_id)
        customers = Customer.objects.filter(business_id=business_id)
        documents = Document.objects.filter(business_id=business_id)
        payments = Payment.objects.filter(business_id=business_id)
    else:
        businesses = Business.objects.all() if tenant_ids is None else Business.objects.filter(tenant_id__in=tenant_ids)
        customers = Customer.objects.all() if tenant_ids is None else Customer.objects.filter(tenant_id__in=tenant_ids)
        documents = Document.objects.all() if tenant_ids is None else Document.objects.filter(tenant_id__in=tenant_ids)
        payments = Payment.objects.all() if tenant_ids is None else Payment.objects.filter(tenant_id__in=tenant_ids)

    total_invoiced = documents.filter(document_type='INVOICE').aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    total_payments = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    outstanding_balances = documents.filter(document_type='INVOICE').aggregate(total=Sum('outstanding_balance'))['total'] or Decimal('0.00')
    overdue_invoices = documents.filter(document_type='INVOICE', status='overdue').count()

    response = {
        'business_count': businesses.count(),
        'active_business_count': businesses.filter(is_active=True).count(),
        'customer_count': customers.count(),
        'total_invoiced': float(total_invoiced),
        'total_payments_received': float(total_payments),
        'outstanding_balances': float(outstanding_balances),
        'overdue_invoices': overdue_invoices,
        'recent_invoices': [],
        'recent_quotations': [],
        'recent_payments': [],
    }

    recent_invoices = documents.filter(document_type='INVOICE').order_by('-created_at')[:5]
    recent_quotations = documents.filter(document_type='QUOTATION').order_by('-created_at')[:5]
    recent_payments = payments.order_by('-payment_date')[:5]

    response['recent_invoices'] = [
        {
            'id': document.id,
            'document_number': document.document_number,
            'customer_name': document.customer.name,
            'total': float(document.total),
            'status': document.status,
            'created_at': document.created_at.isoformat(),
        }
        for document in recent_invoices
    ]
    response['recent_quotations'] = [
        {
            'id': document.id,
            'document_number': document.document_number,
            'customer_name': document.customer.name,
            'total': float(document.total),
            'status': document.status,
            'created_at': document.created_at.isoformat(),
        }
        for document in recent_quotations
    ]
    response['recent_payments'] = [
        {
            'id': payment.id,
            'customer_name': payment.customer.name,
            'amount': float(payment.amount),
            'payment_method': payment.payment_method,
            'payment_date': payment.payment_date.isoformat(),
        }
        for payment in recent_payments
    ]
    return Response(response)
