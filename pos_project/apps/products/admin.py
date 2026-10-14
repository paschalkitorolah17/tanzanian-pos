from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'parent', 'is_active']
    list_filter = ['business', 'is_active']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'barcode', 'category',
        'selling_price', 'cost_price', 'tax_status',
        'is_active', 'business'
    ]
    list_filter = ['business', 'category', 'tax_status', 'is_active']
    search_fields = ['name', 'sku', 'barcode', 'brand']
    list_editable = ['selling_price', 'is_active']
