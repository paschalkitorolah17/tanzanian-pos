"""
Access control decorators for views.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(*roles):
    """
    Allow only users with the given roles (or superuser).
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.role in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to access this page.")
        return _wrapped
    return decorator


def frontline_required(view_func):
    """Cashier + Sales Associate (+ leadership for convenience)."""
    return role_required(
        'cashier', 'sales_associate',
        'business_owner', 'manager'
    )(view_func)


def leadership_required(view_func):
    """Business Owner + Manager + supporting roles."""
    return role_required(
        'business_owner', 'manager',
        'accountant', 'auditor', 'operator'
    )(view_func)
