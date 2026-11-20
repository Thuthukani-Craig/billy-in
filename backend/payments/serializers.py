from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from accounts.tenant_context import resolve_request_tenant
from .models import Payment
from .services import record_payment


class PaymentSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    tenant = serializers.IntegerField(source='tenant_id', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'tenant', 'business', 'business_name', 'customer', 'customer_name',
            'invoice', 'amount', 'payment_date', 'payment_method', 'reference', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at']

    def validate(self, data):
        if self.instance:
            raise serializers.ValidationError('Recorded payments are immutable. Use a future reversal workflow to correct one.')
        business = data.get('business')
        customer = data.get('customer')
        invoice = data.get('invoice')
        request = self.context.get('request')
        if request:
            tenant = resolve_request_tenant(request)
            if business is None or business.tenant_id != tenant.id:
                raise serializers.ValidationError({'business': 'Choose a business in the selected tenant.'})
            if customer is None or customer.tenant_id != tenant.id or customer.business_id != business.id:
                raise serializers.ValidationError({'customer': 'Choose a customer belonging to the selected business.'})
            if invoice and (invoice.tenant_id != tenant.id or invoice.business_id != business.id):
                raise serializers.ValidationError({'invoice': 'Invoice must belong to the selected business.'})
        if invoice and customer and invoice.customer_id != customer.id:
            raise serializers.ValidationError({'invoice': 'Invoice customer must match the payment customer.'})
        return data

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        if request:
            validated_data['tenant'] = resolve_request_tenant(request)
        try:
            return record_payment(**validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, 'message_dict') else exc.messages)

    def update(self, instance, validated_data):
        raise serializers.ValidationError('Recorded payments cannot be edited. Use a reversal workflow to correct one.')
