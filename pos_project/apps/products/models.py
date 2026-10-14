"""
PRODUCT MODELS
==============

Category and Product are the foundation of the catalog.

Key design decisions:
- All money fields use DecimalField (never Float)
- SKU and Barcode are unique per Business
- Soft delete is used so historical sales stay valid
- Tax status and rate are stored on the product (flexible)
"""

from django.db import models
from apps.core.models import TimeStampedModel, SoftDeleteModel, BusinessScopedModel


class Category(TimeStampedModel, SoftDeleteModel, BusinessScopedModel):
    """
    Product category (e.g. Soft Drinks, Electronics, Food, Clothing).
    Supports optional parent for future sub-categories.
    """
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        help_text="Optional parent category for hierarchy"
    )
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'categories'
        unique_together = [('business', 'name')]
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(TimeStampedModel, SoftDeleteModel, BusinessScopedModel):
    """
    A sellable product / item in the catalog.
    """

    TAX_STATUS_CHOICES = [
        ('taxable', 'Taxable'),
        ('zero_rated', 'Zero Rated'),
        ('exempt', 'Exempt'),
    ]

    # Basic information
    name = models.CharField(max_length=255, db_index=True)
    sku = models.CharField(
        max_length=50,
        help_text="Stock Keeping Unit - unique per business"
    )
    barcode = models.CharField(
        max_length=50,
        blank=True,
        help_text="Barcode (EAN/UPC). Leave blank if not used."
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='products'
    )
    brand = models.CharField(max_length=100, blank=True)
    unit = models.CharField(
        max_length=30,
        default='pcs',
        help_text="Unit of measure: pcs, kg, litre, pack, etc."
    )
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True
    )

    # Pricing (all Decimal – never use float for money)
    cost_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Purchase / cost price in TZS"
    )
    selling_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Normal retail selling price in TZS"
    )
    wholesale_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional wholesale price"
    )
    min_selling_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Lowest price a cashier is allowed to sell at"
    )

    # Tax
    tax_status = models.CharField(
        max_length=20,
        choices=TAX_STATUS_CHOICES,
        default='taxable'
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00,
        help_text="VAT percentage to apply when tax_status is taxable"
    )

    # Inventory helpers
    reorder_level = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        help_text="Alert when stock falls to this level"
    )

    class Meta:
        unique_together = [
            ('business', 'sku'),
            ('business', 'barcode'),
        ]
        indexes = [
            models.Index(fields=['business', 'name']),
            models.Index(fields=['business', 'barcode']),
            models.Index(fields=['business', 'sku']),
        ]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_taxable(self):
        return self.tax_status == 'taxable'
