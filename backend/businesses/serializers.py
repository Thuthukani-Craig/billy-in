from rest_framework import serializers

from accounts.models import TenantMembership
from .models import Business


class BusinessSerializer(serializers.ModelSerializer):
    tenant = serializers.IntegerField(read_only=True)

    class Meta:
        model = Business
        fields = [
            'id', 'tenant', 'name', 'trading_name', 'registration_number', 'vat_registration_number',
            'email', 'telephone', 'physical_address', 'postal_address', 'logo',
            'primary_brand_colour', 'banking_institution', 'account_holder', 'account_number',
            'branch_code', 'account_type', 'payment_instructions', 'default_payment_terms',
            'invoice_footer', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and not request.user.is_superuser:
            membership = TenantMembership.objects.filter(user=request.user, is_active=True).order_by('pk').first()
            if membership is None:
                raise serializers.ValidationError({'tenant': 'User is not assigned to any tenant.'})
            tenant = membership.tenant
            if validated_data.get('tenant') and validated_data['tenant'] != tenant:
                raise serializers.ValidationError({'tenant': 'Tenant does not match the authenticated user membership.'})
            validated_data['tenant'] = tenant
        return super().create(validated_data)
