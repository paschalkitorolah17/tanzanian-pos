from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from decimal import Decimal

from .models import Sale, SaleItem, SaleReturn, SaleReturnItem
from .services import ReturnService


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = [
        'product', 'quantity', 'unit_price', 'discount',
        'tax_amount', 'line_total', 'cost_price_at_sale', 'quantity_returned'
    ]
    can_delete = False


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_number', 'branch', 'cashier',
        'grand_total', 'status', 'created_at'
    ]
    list_filter = ['status', 'branch', 'created_at']
    search_fields = ['transaction_number']
    readonly_fields = [
        'transaction_number', 'business', 'branch', 'cashier',
        'subtotal', 'discount_total', 'tax_total', 'grand_total',
        'idempotency_key', 'created_at', 'updated_at'
    ]
    inlines = [SaleItemInline]
    actions = ['process_full_return']

    def has_add_permission(self, request):
        return False

    @admin.action(description="Process FULL return for selected sale(s)")
    def process_full_return(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one sale.", messages.ERROR)
            return

        sale = queryset.first()
        if sale.status in ['cancelled', 'fully_returned']:
            self.message_user(request, f"Sale {sale.transaction_number} cannot be returned.", messages.ERROR)
            return

        items = []
        for si in sale.items.all():
            returnable = si.quantity - si.quantity_returned
            if returnable > 0:
                items.append({
                    'sale_item_id': si.id,
                    'quantity': str(returnable)
                })

        if not items:
            self.message_user(request, "Nothing left to return.", messages.WARNING)
            return

        try:
            ret = ReturnService.create_return(
                original_sale=sale,
                items=items,
                processed_by=request.user,
                reason="Full return via admin",
            )
            self.message_user(
                request,
                f"Return {ret.return_number} created. Refund: TZS {ret.refund_amount}",
                messages.SUCCESS
            )
        except Exception as e:
            self.message_user(request, str(e), messages.ERROR)


class SaleReturnItemInline(admin.TabularInline):
    model = SaleReturnItem
    extra = 0
    readonly_fields = ['sale_item', 'product', 'quantity', 'unit_price', 'line_total']
    can_delete = False


@admin.register(SaleReturn)
class SaleReturnAdmin(admin.ModelAdmin):
    list_display = [
        'return_number', 'original_sale', 'refund_amount',
        'processed_by', 'created_at'
    ]
    list_filter = ['branch', 'created_at']
    search_fields = ['return_number', 'original_sale__transaction_number']
    readonly_fields = [
        'return_number', 'business', 'branch', 'original_sale',
        'refund_amount', 'processed_by', 'created_at'
    ]
    inlines = [SaleReturnItemInline]

    def has_add_permission(self, request):
        return False
