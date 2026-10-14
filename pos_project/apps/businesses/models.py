"""
BUSINESS & BRANCH MODELS
========================

Business = the top-level tenant (a real shop / company).
Branch   = a physical location belonging to that business.
BusinessSettings = configurable rules for that business.

These models are the foundation of multi-tenancy in the system.
"""

from django.db import models
from apps.core.models import TimeStampedModel, SoftDeleteModel


class Business(TimeStampedModel, SoftDeleteModel):
    """
    Represents a real-world business using the POS system.
    Examples: Kittoh Retail Store, Mama Ntilie Shop, Electronics Hub, etc.
    """
    name = models.CharField(max_length=255, help_text="Official business name")
    tin = models.CharField(
        max_length=50,
        blank=True,
        help_text="TIN / VAT registration number (shown on receipts)"
    )
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True, help_text="Physical or postal address")
    logo = models.ImageField(
        upload_to='business_logos/',
        blank=True,
        null=True,
        help_text="Business logo used on receipts and dashboard"
    )
    currency_code = models.CharField(
        max_length=3,
        default='TZS',
        help_text="ISO currency code. Currently only TZS is fully supported."
    )
    vrn = models.CharField(
        max_length=50,
        blank=True,
        help_text="VAT Registration Number (optional)"
    )
    receipt_footer = models.TextField(
        blank=True,
        help_text="Custom text shown at the bottom of receipts (e.g. Asante kwa kununua!)"
    )
    class Meta:
        verbose_name_plural = 'businesses'
        ordering = ['name']

    def __str__(self):
        return self.name


class Branch(TimeStampedModel, SoftDeleteModel):
    """
    A physical outlet / location of a Business.
    A business can have one or many branches.
    """
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='branches'
    )
    name = models.CharField(max_length=100, help_text="e.g. Main Branch, Mwanza Branch")
    code = models.CharField(
        max_length=20,
        help_text="Short unique code inside the business, e.g. HQ, MWZ-01"
    )
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_main = models.BooleanField(
        default=False,
        help_text="Mark the primary/head office branch"
    )

    class Meta:
        verbose_name_plural = 'branches'
        unique_together = [('business', 'code')]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.business.name})"


class BusinessSettings(TimeStampedModel):
    """
    Configurable rules for a Business.

    We keep these separate from the Business model so that
    the core Business table stays clean and settings can grow
    without changing the main model frequently.
    """
    business = models.OneToOneField(
        Business,
        on_delete=models.CASCADE,
        related_name='settings'
    )

    # Stock policy
    allow_negative_stock = models.BooleanField(
        default=False,
        help_text="If False, the system will reject sales that would make stock negative."
    )

    # Discount policy
    max_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.00,
        help_text="Maximum discount a normal cashier can give (percentage)."
    )

    # Tax defaults
    default_tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00,
        help_text="Default VAT rate (%) applied to new products."
    )

    # Receipt settings
    receipt_footer = models.TextField(
        blank=True,
        default="Asante kwa kununua! Karibu tena.",
        help_text="Text shown at the bottom of every receipt."
    )
    receipt_show_tin = models.BooleanField(default=True)

    # Other future flags can be added here (loyalty, multi-currency, etc.)

    def __str__(self):
        return f"Settings for {self.business.name}"


# Temporary note: we will add receipt_footer and vrn cleanly below
