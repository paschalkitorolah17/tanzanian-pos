from django.contrib import admin
from .models import PaymentMethod, Payment

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'business', 'is_cash', 'requires_reference', 'is_active']
    list_filter = ['business', 'is_active']
    search_fields = ['name', 'code']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['sale', 'payment_method', 'amount', 'reference', 'received_by', 'created_at']
    list_filter = ['payment_method', 'created_at']
    search_fields = ['sale__transaction_number', 'reference']
    readonly_fields = ['sale', 'payment_method', 'amount', 'reference', 'received_by', 'created_at']
