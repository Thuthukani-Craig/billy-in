from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'customer_type', 'telephone', 'email', 'is_active')
    list_filter = ('is_active', 'customer_type', 'business')
    search_fields = ('name', 'email', 'telephone', 'contact_person')
