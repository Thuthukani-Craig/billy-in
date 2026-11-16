from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'business', 'invoice', 'amount', 'payment_date', 'payment_method')
    list_filter = ('business', 'payment_method', 'payment_date')
    search_fields = ('customer__name', 'reference')
