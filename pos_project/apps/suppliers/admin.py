from django.contrib import admin
from .models import Supplier

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'business', 'is_active']
    list_filter = ['business', 'is_active']
    search_fields = ['name', 'phone']
