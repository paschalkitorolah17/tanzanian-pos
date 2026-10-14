"""
SALES MODELS
============
Sale, SaleItem, SaleReturn, SaleReturnItem
"""

from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class Sale(TimeStampedModel):
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('partially_returned', 'Partially Returned'),
        ('fully_returned', 'Fully Returned'),
    ]

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.PROTECT,
        related_name='sales'
    )
    branch = models.ForeignKey(
        'businesses.Branch',
        on_delete=models.PROTECT,
        related_name='sales'
    )
    transaction_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True
    )
    customer = models.ForeignKey(
        'customers.Customer',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sales'
    )
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sales'
    )

    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    notes = models.TextField(blank=True)

    idempotency_key = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['branch', 'created_at']),
            models.Index(fields=['cashier', 'created_at']),
            models.Index(fields=['transaction_number']),
        ]

    def __str__(self):
        return self.transaction_number


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='sale_items'
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)
    cost_price_at_sale = models.DecimalField(max_digits=14, decimal_places=2)

    # How many have already been returned
    quantity_returned = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def quantity_returnable(self):
        return self.quantity - self.quantity_returned


class SaleReturn(TimeStampedModel):
    """
    A return document linked to an original Sale.
    Can be full or partial.
    """
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.PROTECT,
        related_name='sale_returns'
    )
    branch = models.ForeignKey(
        'businesses.Branch',
        on_delete=models.PROTECT,
        related_name='sale_returns'
    )
    original_sale = models.ForeignKey(
        Sale,
        on_delete=models.PROTECT,
        related_name='returns'
    )
    return_number = models.CharField(max_length=30, unique=True, db_index=True)

    refund_amount = models.DecimalField(max_digits=14, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='processed_returns'
    )

    # Refund payment method (cash, mpesa, etc.)
    refund_method = models.ForeignKey(
        'payments.PaymentMethod',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    refund_reference = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.return_number


class SaleReturnItem(models.Model):
    sale_return = models.ForeignKey(
        SaleReturn,
        on_delete=models.CASCADE,
        related_name='items'
    )
    sale_item = models.ForeignKey(
        SaleItem,
        on_delete=models.PROTECT,
        related_name='return_items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Return {self.quantity} x {self.product.name}"
