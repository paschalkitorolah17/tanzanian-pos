from django.contrib import admin
from .models import Business, Branch, BusinessSettings


class BranchInline(admin.TabularInline):
    model = Branch
    extra = 1
    fields = ['name', 'code', 'phone', 'is_main', 'is_active']


class BusinessSettingsInline(admin.StackedInline):
    model = BusinessSettings
    can_delete = False
    extra = 0


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['name', 'tin', 'phone', 'currency_code', 'is_active', 'created_at']
    list_filter = ['is_active', 'currency_code']
    search_fields = ['name', 'tin', 'phone', 'email']
    inlines = [BusinessSettingsInline, BranchInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Automatically create default settings if they do not exist
        BusinessSettings.objects.get_or_create(business=obj)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'business', 'is_main', 'is_active']
    list_filter = ['business', 'is_main', 'is_active']
    search_fields = ['name', 'code']
