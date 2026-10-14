from django.contrib import admin
from .models import Warehouse, StockLevel, InventoryTransaction


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch', 'is_default', 'is_active']
    list_filter = ['branch__business', 'is_default']


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ['product', 'branch', 'warehouse', 'quantity', 'updated_at']
    list_filter = ['branch__business', 'branch']
    search_fields = ['product__name', 'product__sku']
    readonly_fields = ['updated_at']


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'transaction_type', 'product',
        'quantity', 'previous_quantity', 'new_quantity',
        'branch', 'created_by'
    ]
    list_filter = ['transaction_type', 'branch__business', 'branch']
    search_fields = ['product__name', 'product__sku', 'reason']
    readonly_fields = [
        'product', 'branch', 'warehouse', 'transaction_type',
        'quantity', 'previous_quantity', 'new_quantity',
        'unit_cost', 'reference_type', 'reference_id',
        'reason', 'notes', 'created_by', 'created_at'
    ]

    def has_add_permission(self, request):
        return False   # Transactions should only be created by the system

    def has_change_permission(self, request, obj=None):
        return False
