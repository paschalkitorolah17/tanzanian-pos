"""
EXPENSE MODELS
==============
"""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel, SoftDeleteModel, BusinessScopedModel


class ExpenseCategory(TimeStampedModel, SoftDeleteModel, BusinessScopedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'expense categories'
        unique_together = [('business', 'name')]
        ordering = ['name']

    def __str__(self):
        return self.name


class Expense(TimeStampedModel):
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.PROTECT,
        related_name='expenses'
    )
    branch = models.ForeignKey(
        'businesses.Branch',
        on_delete=models.PROTECT,
        related_name='expenses',
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name='expenses'
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_method = models.ForeignKey(
        'payments.PaymentMethod',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    date = models.DateField()
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recorded_expenses'
    )
    attachment = models.FileField(
        upload_to='expenses/',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['business', 'date']),
            models.Index(fields=['category', 'date']),
        ]

    def __str__(self):
        return f"{self.category.name} – TZS {self.amount} ({self.date})"
