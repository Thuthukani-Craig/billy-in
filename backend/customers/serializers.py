from rest_framework import serializers

from accounts.models import TenantMembership
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
        business = data.get('business')
        tenant = data.get('tenant')
        if business and tenant and business.tenant_id != tenant:
            raise serializers.ValidationError({'business': 'Business must belong to the same tenant as the customer.'})
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and not request.user.is_superuser:
            membership = TenantMembership.objects.filter(user=request.user, is_active=True).order_by('pk').first()
            if membership is None:
                raise serializers.ValidationError({'tenant': 'User is not assigned to any tenant.'})
            tenant = membership.tenant
            business = validated_data.get('business')
            if business and business.tenant_id != tenant.id:
                raise serializers.ValidationError({'business': 'Business must belong to the same tenant as the customer.'})
            validated_data['tenant'] = tenant
        return super().create(validated_data)
