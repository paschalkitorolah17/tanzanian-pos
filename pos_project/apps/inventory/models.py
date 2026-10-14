"""
INVENTORY MODELS
================

We use a double approach:
1. StockLevel      → fast current quantity (denormalized)
2. InventoryTransaction → full ledger (source of truth)

All stock-changing operations must:
- Run inside transaction.atomic()
- Use select_for_update() to lock the row
- Create an InventoryTransaction record
"""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel, SoftDeleteModel


class Warehouse(TimeStampedModel, SoftDeleteModel):
    """
    A storage location inside a branch.
    Most small shops will have only one (Main Store).
    """
    branch = models.ForeignKey(
        'businesses.Branch',
        on_delete=models.CASCADE,
        related_name='warehouses'
    )
    name = models.CharField(max_length=100, default='Main Store')
    is_default = models.BooleanField(default=True)

    class Meta:
        unique_together = [('branch', 'name')]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class StockLevel(TimeStampedModel):
    """
    Current stock quantity of a product in a specific branch/warehouse.
    This is a denormalized cache for speed.
    The real history lives in InventoryTransaction.
    """
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='stock_levels'
    )
    branch = models.ForeignKey(
        'businesses.Branch',
        on_delete=models.CASCADE,
        related_name='stock_levels'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='stock_levels'
    )
    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=0,
        help_text="Current available quantity"
    )

    class Meta:
        unique_together = [('product', 'branch', 'warehouse')]
        indexes = [
            models.Index(fields=['product', 'branch']),
        ]

    def __str__(self):
        return f"{self.product.name} @ {self.branch.name}: {self.quantity}"


class InventoryTransaction(TimeStampedModel):
    """
    The inventory ledger – every stock movement is recorded here.
    This is the source of truth for stock history.
    """

    TRANSACTION_TYPES = [
        ('opening', 'Opening Stock'),
        ('purchase', 'Purchase Receipt'),
        ('sale', 'Sale'),
        ('sale_return', 'Sale Return'),
        ('adjustment', 'Stock Adjustment'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
        ('damage', 'Damage / Write-off'),
        ('correction', 'Correction'),
    ]

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='inventory_transactions'
    )
    branch = models.ForeignKey(
        'businesses.Branch',
        on_delete=models.PROTECT,
        related_name='inventory_transactions'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)

    # Quantity change (positive = in, negative = out)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)

    previous_quantity = models.DecimalField(max_digits=14, decimal_places=3)
    new_quantity = models.DecimalField(max_digits=14, decimal_places=3)

    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost at the time of this transaction (for valuation)"
    )

    # Reference to the document that caused this movement
    reference_type = models.CharField(max_length=50, blank=True)  # 'sale', 'purchase', etc.
    reference_id = models.PositiveIntegerField(null=True, blank=True)

    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='inventory_transactions'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'branch', 'created_at']),
            models.Index(fields=['reference_type', 'reference_id']),
            models.Index(fields=['transaction_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} | {self.product.name} | {self.quantity}"
