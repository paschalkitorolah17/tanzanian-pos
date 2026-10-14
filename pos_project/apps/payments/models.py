"""
PAYMENT MODELS
==============

Supports multiple payment methods and split/mixed payments.
A single Sale can have several Payment rows (e.g. Cash + M-Pesa).
"""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel, SoftDeleteModel, BusinessScopedModel


class PaymentMethod(TimeStampedModel, SoftDeleteModel, BusinessScopedModel):
    """
    Configurable payment methods per business.
    Examples: Cash, M-Pesa, Airtel Money, Mixx by Yas, HaloPesa, Bank, Card
    """
    name = models.CharField(max_length=50)          # Display name
    code = models.CharField(max_length=20)          # Internal code: cash, mpesa, airtel...
    is_cash = models.BooleanField(default=False)
    requires_reference = models.BooleanField(
        default=False,
        help_text="True for mobile money / bank (needs transaction code)"
    )
    sort_order = models.PositiveIntegerField(default=10)

    class Meta:
        unique_together = [('business', 'code')]
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Payment(TimeStampedModel):
    """
    One payment line belonging to a Sale.
    """
    sale = models.ForeignKey(
        'sales.Sale',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="M-Pesa code, bank reference, etc."
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='payments_received'
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.payment_method.name}: {self.amount}"
