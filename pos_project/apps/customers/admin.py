from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'business', 'is_active']
    list_filter = ['business', 'is_active']
    search_fields = ['name', 'phone', 'email']
