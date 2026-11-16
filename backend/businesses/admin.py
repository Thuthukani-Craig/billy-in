from django.contrib import admin

from .models import Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'trading_name', 'email', 'telephone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'email', 'registration_number')
