"""
ACCOUNTS MODELS
===============

Custom User model with refined RBAC for Tanzanian POS.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for the POS system.

    Role families:
    1. Store Leadership  → business_owner, manager
    2. Frontline Sales   → cashier, sales_associate
    3. Operations        → operator
    """

    class Role(models.TextChoices):
        # Store Leadership
        BUSINESS_OWNER = 'business_owner', 'Business Owner'
        MANAGER = 'manager', 'Manager'

        # Frontline Sales
        CASHIER = 'cashier', 'Cashier'
        SALES_ASSOCIATE = 'sales_associate', 'Sales Associate'

        # Operations
        OPERATOR = 'operator', 'Operator'

        # Optional supporting roles (kept for flexibility)
        ACCOUNTANT = 'accountant', 'Accountant'
        AUDITOR = 'auditor', 'Auditor'
        SUPER_ADMIN = 'super_admin', 'Super Administrator'

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.CASHIER,
        help_text="Primary role of this user"
    )

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='users',
        help_text="The business this user belongs to. Null only for Super Admins."
    )

    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # ------------------------------------------------------------------
    # Role helpers
    # ------------------------------------------------------------------
    @property
    def is_store_leadership(self):
        return self.role in [self.Role.BUSINESS_OWNER, self.Role.MANAGER]

    @property
    def is_frontline(self):
        return self.role in [self.Role.CASHIER, self.Role.SALES_ASSOCIATE]

    @property
    def is_operator(self):
        return self.role == self.Role.OPERATOR

    @property
    def can_access_pos(self):
        """Who is allowed to use the POS screen."""
        return self.is_frontline or self.is_store_leadership or self.is_superuser

    @property
    def can_access_dashboard(self):
        """Who is allowed to see the main dashboard."""
        return (
            self.is_store_leadership
            or self.role in [self.Role.ACCOUNTANT, self.Role.AUDITOR, self.Role.OPERATOR]
            or self.is_superuser
        )
