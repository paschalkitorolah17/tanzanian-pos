from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'role', 'business', 'is_active', 'is_staff'
    ]
    list_filter = ['role', 'is_active', 'is_staff', 'business']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone']
    ordering = ['username']

    # Safer way to extend fieldsets
    fieldsets = list(BaseUserAdmin.fieldsets) + [
        ('POS Information', {
            'fields': ('role', 'business', 'phone'),
        }),
    ]

    add_fieldsets = list(BaseUserAdmin.add_fieldsets) + [
        ('POS Information', {
            'fields': ('role', 'business', 'phone'),
        }),
    ]
