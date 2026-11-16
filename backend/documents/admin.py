from django.contrib import admin

from .models import Document, DocumentLineItem


class DocumentLineItemInline(admin.TabularInline):
    model = DocumentLineItem
    extra = 1


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    inlines = [DocumentLineItemInline]
    list_display = ('document_number', 'business', 'customer', 'document_type', 'status', 'total')
    list_filter = ('document_type', 'status', 'business')
    search_fields = ('document_number', 'customer__name')
