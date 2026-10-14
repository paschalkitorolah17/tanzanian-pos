from django.contrib import admin
from .models import Purchase, PurchaseItem

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'supplier', 'branch', 'total_cost', 'status', 'received_by', 'created_at']
    list_filter = ['status', 'branch', 'created_at']
    inlines = [PurchaseItemInline]
