"""
CORE BASE MODELS
================

These abstract models are the foundation of the entire POS system.
Every important domain model will inherit from one or more of them.

WHY abstract models?
- Consistent timestamps, soft-delete behaviour, and business scoping
  without repeating the same fields in every model (DRY principle).
- Changes to common behaviour happen in only one place.
"""

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Provides automatic created_at and updated_at timestamps.

    created_at  → set once when the row is first inserted.
    updated_at  → updated automatically on every save().

    Both fields are indexed because we frequently filter and
    order by date (reports, dashboards, audit queries).
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when this record was first created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this record was last modified."
    )

    class Meta:
        abstract = True   # This model does NOT create its own database table


class SoftDeleteModel(models.Model):
    """
    Implements soft deletion instead of physical DELETE.

    WHY soft delete?
    - Sales, products, customers etc. are referenced by historical
      transactions. Physically deleting them would break foreign keys
      and destroy auditability.
    - is_active = False means "hidden from normal UI" but the record
      still exists for reports and history.
    """
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="If False, the record is considered deleted (soft delete)."
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the record was soft-deleted. Null if still active."
    )

    def soft_delete(self):
        """
        Mark the record as inactive instead of removing it from the database.
        """
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at', 'updated_at'])

    def restore(self):
        """Bring a soft-deleted record back to life."""
        self.is_active = True
        self.deleted_at = None
        self.save(update_fields=['is_active', 'deleted_at', 'updated_at'])

    class Meta:
        abstract = True


class BusinessScopedModel(models.Model):
    """
    Every record that belongs to a specific business inherits this.

    WHY?
    - Multi-tenancy readiness from day one.
    - Future SaaS: one database can host many businesses safely.
    - Security: every query can filter by business so data never leaks.
    """
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.PROTECT,          # Prevent accidental deletion of a business that still has data
        related_name='%(class)ss',
        help_text="The business that owns this record."
    )

    class Meta:
        abstract = True
