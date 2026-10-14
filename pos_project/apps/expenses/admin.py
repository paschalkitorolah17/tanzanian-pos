from django.contrib import admin
from .models import ExpenseCategory, Expense


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'is_active']
    list_filter = ['business', 'is_active']
    search_fields = ['name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'category', 'amount', 'branch',
        'payment_method', 'recorded_by', 'created_at'
    ]
    list_filter = ['category', 'branch', 'date']
    search_fields = ['description', 'reference']
    date_hierarchy = 'date'
