from django.db import transaction
from rest_framework import serializers

from accounts.tenant_context import resolve_request_tenant
from businesses.models import Business
from .models import Document, DocumentLineItem, DocumentDesignProfile
from .snapshots import capture_issued_snapshot


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
        read_only_fields = [
            'id', 'tenant', 'document_number', 'subtotal', 'discount_amount', 'tax_amount',
            'total', 'amount_paid', 'outstanding_balance', 'created_at', 'updated_at',
        ]

    def validate(self, data):
        business = data.get('business') or getattr(self.instance, 'business', None)
        customer = data.get('customer') or getattr(self.instance, 'customer', None)
        document_type = data.get('document_type') or getattr(self.instance, 'document_type', None)
        if business and customer and customer.business_id != business.id:
            raise serializers.ValidationError({'customer': 'Customer must belong to the selected business.'})
        request = self.context.get('request')
        if request and business:
            tenant = resolve_request_tenant(request)
            if business.tenant_id != tenant.id:
                raise serializers.ValidationError({'business': 'Business must belong to the selected tenant.'})
            if customer and customer.tenant_id != tenant.id:
                raise serializers.ValidationError({'customer': 'Customer must belong to the selected tenant.'})
        payment = data.get('payment', getattr(self.instance, 'payment', None))
        if document_type == 'RECEIPT' and payment is None:
            raise serializers.ValidationError({'payment': 'Receipts must be linked to an actual payment record.'})
        if payment and (business is None or customer is None or payment.business_id != business.id or payment.customer_id != customer.id):
            raise serializers.ValidationError({'payment': 'Receipt payment must belong to the same business and customer.'})
        if payment and business and payment.tenant_id != business.tenant_id:
            raise serializers.ValidationError({'payment': 'Receipt payment must belong to the selected tenant.'})
        requested_status = data.get('status')
        if self.instance is None:
            if requested_status and requested_status not in (Document.STATUS_DRAFT, Document.STATUS_ISSUED):
                raise serializers.ValidationError({'status': 'New documents must begin as draft or issued.'})
            if document_type == 'RECEIPT' and requested_status not in (None, Document.STATUS_ISSUED):
                raise serializers.ValidationError({'status': 'Receipts are created as issued records.'})
        elif requested_status and requested_status != self.instance.status:
            allowed = {
                Document.DOCUMENT_TYPE_QUOTATION: {
                    Document.STATUS_DRAFT: {Document.STATUS_ISSUED, Document.STATUS_CANCELLED},
                    Document.STATUS_ISSUED: {Document.STATUS_ACCEPTED, Document.STATUS_REJECTED, Document.STATUS_EXPIRED, Document.STATUS_CANCELLED},
                },
                Document.DOCUMENT_TYPE_INVOICE: {
                    Document.STATUS_DRAFT: {Document.STATUS_ISSUED, Document.STATUS_CANCELLED},
                    Document.STATUS_ISSUED: {Document.STATUS_CANCELLED},
                },
            }
            permitted = allowed.get(self.instance.document_type, {}).get(self.instance.status, set())
            if requested_status not in permitted:
                raise serializers.ValidationError({'status': 'This document status transition is not permitted.'})
        if self.instance and self.instance.document_type == 'RECEIPT':
            raise serializers.ValidationError('Issued receipt records cannot be edited.')
        return data

    def _generate_document_number(self, business, document_type):
        sequence_fields = {
            'QUOTATION': ('QUO', 'next_quotation_number'),
            'INVOICE': ('INV', 'next_invoice_number'),
            'RECEIPT': ('REC', 'next_receipt_number'),
        }
        prefix, field_name = sequence_fields[document_type]
        with transaction.atomic():
            locked_business = Business.objects.select_for_update().get(pk=business.pk)
            sequence = getattr(locked_business, field_name)
            setattr(locked_business, field_name, sequence + 1)
            locked_business.save(update_fields=[field_name])
            return f'{locked_business.business_code}-{prefix}-{sequence:04d}'

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        if request:
            tenant = resolve_request_tenant(request)
            business = validated_data.get('business')
            customer = validated_data.get('customer')
            if business is None or business.tenant_id != tenant.id:
                raise serializers.ValidationError({'business': 'Choose a business in the selected tenant.'})
            if customer is None or customer.tenant_id != tenant.id or customer.business_id != business.id:
                raise serializers.ValidationError({'customer': 'Choose a customer belonging to the selected business.'})
            validated_data['tenant'] = tenant

        line_items_data = validated_data.pop('line_items', [])
        if validated_data.get('document_type') == Document.DOCUMENT_TYPE_RECEIPT:
            payment = validated_data.get('payment')
            validated_data.setdefault('status', Document.STATUS_ISSUED)
            validated_data['amount_paid'] = payment.amount
            if not line_items_data:
                line_items_data = [{
                    'description': f"Payment received ({payment.reference or payment.pk})",
                    'quantity': 1,
                    'unit_price': payment.amount,
                    'discount': 0,
                    'tax_rate': 0,
                }]
        document = Document(**validated_data)
        if not document.document_number:
            document.document_number = self._generate_document_number(document.business, document.document_type)
        document.save()
        for item_data in line_items_data:
            DocumentLineItem.objects.create(document=document, **item_data)
        document.refresh_from_db()
        if document.status != Document.STATUS_DRAFT:
            capture_issued_snapshot(document)
        return document

    @transaction.atomic
    def update(self, instance, validated_data):
        line_items_data = validated_data.pop('line_items', None)
        if instance.status not in (Document.STATUS_DRAFT,):
            protected = {'business', 'customer', 'document_type', 'document_number'}
            if protected.intersection(validated_data) or line_items_data is not None:
                raise serializers.ValidationError('Only draft documents can change their parties or line items.')
        instance = super().update(instance, validated_data)
        if line_items_data is not None:
            instance.line_items.all().delete()
            for item_data in line_items_data:
                DocumentLineItem.objects.create(document=instance, **item_data)
        instance.save()
        if instance.status != Document.STATUS_DRAFT:
            capture_issued_snapshot(instance)
        return instance



class DocumentDesignProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentDesignProfile
        fields = [
            "id", "business", "document_type", "theme", "primary_colour",
            "show_logo", "show_payment_details", "show_business_registration",
            "show_customer_vat_number", "design_tokens", "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]

    def validate_design_tokens(self, value):
        allowed = {"accent_colour", "muted_colour", "font_scale", "corner_style"}
        if not isinstance(value, dict) or set(value) - allowed:
            raise serializers.ValidationError("Only approved design tokens may be configured.")
        for key in ("accent_colour", "muted_colour"):
            colour = value.get(key)
            if colour and (not isinstance(colour, str) or len(colour) != 7 or not colour.startswith("#") or any(ch not in "0123456789abcdefABCDEF" for ch in colour[1:])):
                raise serializers.ValidationError(f"{key} must be a six-digit hexadecimal colour.")
        if "font_scale" in value:
            try:
                scale = float(value["font_scale"])
            except (TypeError, ValueError):
                raise serializers.ValidationError("font_scale must be between 0.8 and 1.2.")
            if not 0.8 <= scale <= 1.2:
                raise serializers.ValidationError("font_scale must be between 0.8 and 1.2.")
        if value.get("corner_style", "square") not in ("square", "soft"):
            raise serializers.ValidationError("corner_style must be square or soft.")
        return value

    def validate(self, data):
        business = data.get("business") or getattr(self.instance, "business", None)
        request = self.context.get("request")
        if request and business:
            tenant = resolve_request_tenant(request)
            if business.tenant_id != tenant.id:
                raise serializers.ValidationError({"business": "Business must belong to the selected tenant."})
        return data
