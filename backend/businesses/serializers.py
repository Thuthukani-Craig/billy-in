from rest_framework import serializers

from accounts.tenant_context import resolve_request_tenant
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
        if request:
            validated_data['tenant'] = resolve_request_tenant(request)
        return super().create(validated_data)
