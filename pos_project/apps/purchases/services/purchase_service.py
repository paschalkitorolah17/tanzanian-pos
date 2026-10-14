"""
PURCHASE SERVICE
================
Receives stock from supplier and updates inventory atomically.
"""

from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.purchases.models import Purchase, PurchaseItem
from apps.inventory.services import StockService
from apps.inventory.models import Warehouse
from apps.products.models import Product


class PurchaseService:

    @staticmethod
    @transaction.atomic
    def receive_stock(
        *,
        branch,
        received_by,
        items: list,          # [{'product_id': 1, 'quantity': '10', 'unit_cost': '5000'}, ...]
        supplier=None,
        reference: str = '',
        notes: str = '',
    ) -> Purchase:
        if not items:
            raise ValidationError("No items to receive.")

        warehouse = Warehouse.objects.filter(
            branch=branch, is_default=True, is_active=True
        ).first()

        total_cost = Decimal('0.00')
        prepared = []

        for entry in items:
            product = Product.objects.get(
                id=entry['product_id'],
                business=branch.business,
                is_active=True
            )
            qty = Decimal(str(entry['quantity']))
            unit_cost = Decimal(str(entry['unit_cost']))

            if qty <= 0:
                raise ValidationError(f"Quantity must be positive for {product.name}")

            line_total = (qty * unit_cost).quantize(Decimal('0.01'))
            total_cost += line_total

            prepared.append({
                'product': product,
                'quantity': qty,
                'unit_cost': unit_cost,
                'line_total': line_total,
            })

        purchase = Purchase.objects.create(
            business=branch.business,
            branch=branch,
            supplier=supplier,
            reference=reference,
            notes=notes,
            total_cost=total_cost,
            received_by=received_by,
            status='received',
        )

        for item in prepared:
            PurchaseItem.objects.create(
                purchase=purchase,
                product=item['product'],
                quantity=item['quantity'],
                unit_cost=item['unit_cost'],
                line_total=item['line_total'],
            )

            # Increase stock
            StockService.adjust_stock(
                product=item['product'],
                branch=branch,
                quantity=item['quantity'],
                transaction_type='purchase',
                user=received_by,
                warehouse=warehouse,
                unit_cost=item['unit_cost'],
                reference_type='purchase',
                reference_id=purchase.id,
                reason=f"Purchase #{purchase.id}",
            )

            # Optionally update product cost price
            if item['unit_cost'] > 0:
                product.cost_price = item['unit_cost']
                product.save(update_fields=['cost_price', 'updated_at'])

        return purchase
