"""
Permission helpers – single place for role checks.
Always enforce these on the backend.
"""

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def role_required(*allowed_roles):
    """
    Decorator for views.
    Usage:
        @role_required('business_owner', 'manager')
        def my_view(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to perform this action.")
        return _wrapped_view
    return decorator


# ------------------------------------------------------------------
# High-level capability checks
# ------------------------------------------------------------------

def user_can_manage_products(user):
    if user.is_superuser:
        return True
    return user.role in ['business_owner', 'manager', 'operator']


def user_can_manage_inventory(user):
    if user.is_superuser:
        return True
    return user.role in ['business_owner', 'manager', 'operator']


def user_can_make_sales(user):
    if user.is_superuser:
        return True
    return user.role in [
        'business_owner', 'manager',
        'cashier', 'sales_associate',
        'operator'          # for web/online orders
    ]


def user_can_apply_discounts(user):
    if user.is_superuser:
        return True
    return user.role in ['business_owner', 'manager', 'cashier', 'sales_associate']


def user_can_view_reports(user):
    if user.is_superuser:
        return True
    return user.role in [
        'business_owner', 'manager',
        'accountant', 'auditor', 'operator'
    ]


def user_can_manage_employees(user):
    if user.is_superuser:
        return True
    return user.role in ['business_owner', 'manager']


def user_can_manage_settings(user):
    if user.is_superuser:
        return True
    return user.role in ['business_owner', 'manager']
