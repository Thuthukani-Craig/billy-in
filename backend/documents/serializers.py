from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from accounts.models import TenantMembership
from businesses.models import Business
from .models import Document, DocumentLineItem


class DocumentLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentLineItem
        fields = [
            'id', 'description', 'quantity', 'unit_of_measure', 'unit_price',
            'discount', 'tax_rate', 'line_subtotal', 'line_tax', 'line_total',
        ]
        read_only_fields = ['id', 'line_subtotal', 'line_tax', 'line_total']


class DocumentSerializer(serializers.ModelSerializer):
    line_items = DocumentLineItemSerializer(many=True, required=False)
    business_name = serializers.CharField(source='business.name', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    tenant = serializers.IntegerField(source='tenant_id', read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'tenant', 'business', 'business_name', 'customer', 'customer_name', 'document_type',
            'document_number', 'status', 'issue_date', 'due_date', 'notes',
            'subtotal', 'discount_amount', 'tax_amount', 'total', 'amount_paid', 'outstanding_balance',
            'line_items', 'payment', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'subtotal', 'discount_amount', 'tax_amount', 'total', 'amount_paid', 'outstanding_balance', 'created_at', 'updated_at']
        extra_kwargs = {
            'document_number': {'required': False, 'allow_blank': True},
        }

    def validate(self, data):
        business = data.get('business')
        customer = data.get('customer')
        tenant = data.get('tenant')
        if business and customer and customer.business_id != business.id:
            raise serializers.ValidationError({'customer': 'Customer must belong to the selected business.'})
        if business and tenant and business.tenant_id != tenant:
            raise serializers.ValidationError({'business': 'Business must belong to the same tenant as the document.'})
        if customer and tenant and customer.tenant_id != tenant:
            raise serializers.ValidationError({'customer': 'Customer must belong to the same tenant as the document.'})
        if data.get('document_type') == 'RECEIPT' and not data.get('payment'):
            raise serializers.ValidationError({'payment': 'Receipts must be linked to an actual payment record.'})
        return data

    def _generate_document_number(self, business, document_type):
        if document_type != 'QUOTATION':
            return None
        with transaction.atomic():
            business_obj = Business.objects.select_for_update().get(pk=business.pk)
            code = business_obj.business_code
            next_number = business_obj.next_quotation_number
            document_number = f'{code}-QUO-{next_number:04d}'
            business_obj.next_quotation_number = next_number + 1
            business_obj.save(update_fields=['next_quotation_number'])
            return document_number

    def create(self, validated_data):
        request = self.context.get('request')
        if request and not request.user.is_superuser:
            membership = TenantMembership.objects.filter(user=request.user, is_active=True).order_by('pk').first()
            if membership is None:
                raise serializers.ValidationError({'tenant': 'User is not assigned to any tenant.'})
            tenant = membership.tenant
            business = validated_data.get('business')
            customer = validated_data.get('customer')
            if business and business.tenant_id != tenant.id:
                raise serializers.ValidationError({'business': 'Business must belong to the same tenant as the document.'})
            if customer and customer.tenant_id != tenant.id:
                raise serializers.ValidationError({'customer': 'Customer must belong to the same tenant as the document.'})
            validated_data['tenant'] = tenant

        line_items_data = validated_data.pop('line_items', [])
        document = Document(**validated_data)
        if not document.document_number:
            document_number = self._generate_document_number(document.business, document.document_type)
            if document_number:
                document.document_number = document_number
        if document.document_number:
            if Document.objects.filter(tenant=document.tenant, document_number=document.document_number).exists():
                raise serializers.ValidationError({'document_number': 'Quotation number already exists for this tenant.'})

        document.save()
        for item_data in line_items_data:
            DocumentLineItem.objects.create(document=document, **item_data)
        document.refresh_from_db()
        return document

    def update(self, instance, validated_data):
        line_items_data = validated_data.pop('line_items', None)
        instance = super().update(instance, validated_data)
        if line_items_data is not None:
            instance.line_items.all().delete()
            for item_data in line_items_data:
                DocumentLineItem.objects.create(document=instance, **item_data)
        instance.save()
        return instance
