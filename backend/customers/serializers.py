from rest_framework import serializers

from accounts.tenant_context import resolve_request_tenant
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    tenant = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'tenant', 'business', 'business_name', 'customer_type', 'name', 'contact_person',
            'email', 'telephone', 'alternative_telephone', 'physical_address', 'billing_address',
            'vat_number', 'notes', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']

    def validate(self, data):
        business = data.get('business') or getattr(self.instance, 'business', None)
        if business and self.instance and business.tenant_id != self.instance.tenant_id:
            raise serializers.ValidationError({'business': 'Customer cannot be moved to a different tenant.'})
        request = self.context.get('request')
        if request and business:
            tenant = resolve_request_tenant(request)
            if business.tenant_id != tenant.id:
                raise serializers.ValidationError({'business': 'Business must belong to the selected tenant.'})
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request:
            tenant = resolve_request_tenant(request)
            business = validated_data.get('business')
            if business is None or business.tenant_id != tenant.id:
                raise serializers.ValidationError({'business': 'Choose a business in the selected tenant.'})
            validated_data['tenant'] = tenant
        return super().create(validated_data)
