"""
STOCK SERVICE
=============

This is the single source of truth for all stock changes.

IMPORTANT RULES:
1. Never update StockLevel directly from views or other apps.
2. Always go through this service.
3. Every change must create an InventoryTransaction.
4. Use select_for_update() + transaction.atomic() to prevent race conditions.
5. Respect the business setting "allow_negative_stock".
"""

from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.inventory.models import StockLevel, InventoryTransaction, Warehouse
from apps.businesses.models import BusinessSettings


class StockService:
    """
    Service responsible for all inventory movements.
    """

    @staticmethod
    @transaction.atomic
    def adjust_stock(
        *,
        product,
        branch,
        quantity: Decimal,
        transaction_type: str,
        user,
        warehouse=None,
        unit_cost=None,
        reference_type: str = '',
        reference_id: int = None,
        reason: str = '',
        notes: str = '',
        allow_negative: bool = None,   # override business setting if needed
    ):
        """
        Change stock for a product in a branch.

        Parameters
        ----------
        product : Product instance
        branch : Branch instance
        quantity : Decimal
            Positive = stock in, Negative = stock out
        transaction_type : str
            One of InventoryTransaction.TRANSACTION_TYPES
        user : User who performs the action
        warehouse : optional Warehouse
        unit_cost : optional cost at the time of movement
        reference_type / reference_id : link to Sale, Purchase, etc.
        reason / notes : human readable explanation
        allow_negative : force allow or deny negative stock

        Returns
        -------
        InventoryTransaction instance
        """

        if quantity == 0:
            raise ValidationError("Quantity change cannot be zero.")

        # ----------------------------------------------------------
        # 1. Get or create the StockLevel row and lock it
        # ----------------------------------------------------------
        stock_level, created = StockLevel.objects.select_for_update().get_or_create(
            product=product,
            branch=branch,
            warehouse=warehouse,
            defaults={'quantity': Decimal('0')}
        )

        previous_qty = stock_level.quantity
        new_qty = previous_qty + quantity

        # ----------------------------------------------------------
        # 2. Check negative stock policy
        # ----------------------------------------------------------
        if allow_negative is None:
            # Read from business settings
            try:
                settings = branch.business.settings
                allow_negative = settings.allow_negative_stock
            except BusinessSettings.DoesNotExist:
                allow_negative = False

        if new_qty < 0 and not allow_negative:
            raise ValidationError(
                f"Insufficient stock for '{product.name}'. "
                f"Available: {previous_qty}, Requested change: {quantity}"
            )

        # ----------------------------------------------------------
        # 3. Update the StockLevel
        # ----------------------------------------------------------
        stock_level.quantity = new_qty
        stock_level.save(update_fields=['quantity', 'updated_at'])

        # ----------------------------------------------------------
        # 4. Create the ledger record
        # ----------------------------------------------------------
        movement = InventoryTransaction.objects.create(
            product=product,
            branch=branch,
            warehouse=warehouse,
            transaction_type=transaction_type,
            quantity=quantity,
            previous_quantity=previous_qty,
            new_quantity=new_qty,
            unit_cost=unit_cost or product.cost_price,
            reference_type=reference_type,
            reference_id=reference_id,
            reason=reason,
            notes=notes,
            created_by=user,
        )

        return movement

    @staticmethod
    def get_current_stock(product, branch, warehouse=None) -> Decimal:
        """Return current quantity (0 if no record exists)."""
        try:
            stock = StockLevel.objects.get(
                product=product,
                branch=branch,
                warehouse=warehouse
            )
            return stock.quantity
        except StockLevel.DoesNotExist:
            return Decimal('0')

    @staticmethod
    @transaction.atomic
    def set_opening_stock(*, product, branch, quantity: Decimal, user, warehouse=None, notes=''):
        """
        Convenience method to set opening stock.
        """
        current = StockService.get_current_stock(product, branch, warehouse)
        difference = quantity - current

        if difference == 0:
            return None

        return StockService.adjust_stock(
            product=product,
            branch=branch,
            quantity=difference,
            transaction_type='opening',
            user=user,
            warehouse=warehouse,
            reason='Opening stock',
            notes=notes,
            allow_negative=True,   # opening stock may start from any value
        )
