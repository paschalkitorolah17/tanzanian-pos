"""
PURCHASE / GOODS RECEIVED
=========================
Simplified for v1: we record stock received + update inventory.
"""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class Purchase(TimeStampedModel):
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.PROTECT,
        related_name='purchases'
    )
    branch = models.ForeignKey(
        'businesses.Branch',
        on_delete=models.PROTECT,
        related_name='purchases'
    )
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.PROTECT,
        related_name='purchases',
        null=True,
        blank=True
    )
    reference = models.CharField(
        max_length=50,
        blank=True,
        help_text="Supplier invoice / delivery note number"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    notes = models.TextField(blank=True)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='purchases_received'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"PO-{self.id} ({self.created_at.date()})"


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
