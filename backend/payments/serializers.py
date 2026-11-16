from rest_framework import serializers

from accounts.models import TenantMembership
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    tenant = serializers.IntegerField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'tenant', 'business', 'business_name', 'customer', 'customer_name',
            'invoice', 'amount', 'payment_date', 'payment_method', 'reference', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at']

    def validate(self, data):
        business = data.get('business')
        customer = data.get('customer')
        invoice = data.get('invoice')
        tenant = data.get('tenant')
        if business and tenant and business.tenant_id != tenant:
            raise serializers.ValidationError({'business': 'Business must belong to the same tenant as the payment.'})
        if customer and tenant and customer.tenant_id != tenant:
            raise serializers.ValidationError({'customer': 'Customer must belong to the same tenant as the payment.'})
        if invoice and tenant and invoice.tenant_id != tenant:
            raise serializers.ValidationError({'invoice': 'Invoice must belong to the same tenant as the payment.'})
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and not request.user.is_superuser:
            membership = TenantMembership.objects.filter(user=request.user, is_active=True).order_by('pk').first()
            if membership is None:
                raise serializers.ValidationError({'tenant': 'User is not assigned to any tenant.'})
            tenant = membership.tenant
            business = validated_data.get('business')
            customer = validated_data.get('customer')
            invoice = validated_data.get('invoice')
            if business and business.tenant_id != tenant.id:
                raise serializers.ValidationError({'business': 'Business must belong to the same tenant as the payment.'})
            if customer and customer.tenant_id != tenant.id:
                raise serializers.ValidationError({'customer': 'Customer must belong to the same tenant as the payment.'})
            if invoice and invoice.tenant_id != tenant.id:
                raise serializers.ValidationError({'invoice': 'Invoice must belong to the same tenant as the payment.'})
            validated_data['tenant'] = tenant
        return super().create(validated_data)
