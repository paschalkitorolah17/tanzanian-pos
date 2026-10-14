"""
RETURN SERVICE
==============

Handles full and partial sales returns.

Rules:
- Always linked to an original Sale
- Stock is restored
- Original Sale status is updated
- Everything runs inside one database transaction
"""

from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.sales.models import Sale, SaleItem, SaleReturn, SaleReturnItem
from apps.inventory.services import StockService
from apps.inventory.models import Warehouse
from apps.payments.models import PaymentMethod


class ReturnService:

    @staticmethod
    def _generate_return_number(branch) -> str:
        today = timezone.localdate()
        prefix = f"RET-{today.strftime('%Y%m%d')}"

        last = SaleReturn.objects.filter(
            business=branch.business,
            return_number__startswith=prefix
        ).order_by('-return_number').first()

        if last:
            try:
                last_seq = int(last.return_number.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1

        return f"{prefix}-{next_seq:06d}"

    @staticmethod
    @transaction.atomic
    def create_return(
        *,
        original_sale: Sale,
        items: list,          # [{'sale_item_id': 1, 'quantity': '2'}, ...]
        processed_by,
        reason: str = '',
        notes: str = '',
        refund_method: PaymentMethod = None,
        refund_reference: str = '',
    ) -> SaleReturn:
        """
        Process a full or partial return.

        items example:
        [
            {'sale_item_id': 10, 'quantity': '1'},
            {'sale_item_id': 12, 'quantity': '2'},
        ]
        """

        if original_sale.status == 'cancelled':
            raise ValidationError("Cannot return a cancelled sale.")

        if not items:
            raise ValidationError("No items to return.")

        branch = original_sale.branch
        warehouse = Warehouse.objects.filter(
            branch=branch,
            is_default=True,
            is_active=True
        ).first()

        # Load original sale items
        sale_items = {
            si.id: si for si in original_sale.items.select_related('product').all()
        }

        calculated = []
        refund_total = Decimal('0.00')

        for entry in items:
            sale_item_id = entry['sale_item_id']
            qty = Decimal(str(entry['quantity']))

            if sale_item_id not in sale_items:
                raise ValidationError(f"Invalid sale item ID: {sale_item_id}")

            sale_item = sale_items[sale_item_id]

            if qty <= 0:
                raise ValidationError(f"Return quantity must be positive for {sale_item.product.name}")

            if qty > sale_item.quantity_returnable:
                raise ValidationError(
                    f"Cannot return {qty} of {sale_item.product.name}. "
                    f"Only {sale_item.quantity_returnable} remaining."
                )

            # Calculate refund for this line (proportional)
            # Simple approach: unit price after discount
            line_net = sale_item.line_total / sale_item.quantity
            line_refund = (line_net * qty).quantize(Decimal('0.01'))

            calculated.append({
                'sale_item': sale_item,
                'product': sale_item.product,
                'quantity': qty,
                'unit_price': sale_item.unit_price,
                'line_total': line_refund,
            })
            refund_total += line_refund

        # Create the Return header
        sale_return = SaleReturn.objects.create(
            business=original_sale.business,
            branch=branch,
            original_sale=original_sale,
            return_number=ReturnService._generate_return_number(branch),
            refund_amount=refund_total,
            reason=reason,
            notes=notes,
            processed_by=processed_by,
            refund_method=refund_method,
            refund_reference=refund_reference,
        )

        # Create return items + restore stock + update original sale items
        for item in calculated:
            SaleReturnItem.objects.create(
                sale_return=sale_return,
                sale_item=item['sale_item'],
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                line_total=item['line_total'],
            )

            # Update quantity_returned on original SaleItem
            sale_item = item['sale_item']
            sale_item.quantity_returned += item['quantity']
            sale_item.save(update_fields=['quantity_returned'])

            # Restore stock
            StockService.adjust_stock(
                product=item['product'],
                branch=branch,
                quantity=item['quantity'],          # positive = stock in
                transaction_type='sale_return',
                user=processed_by,
                warehouse=warehouse,
                reference_type='sale_return',
                reference_id=sale_return.id,
                reason=f"Return {sale_return.return_number}",
            )

        # Update original Sale status
        all_items = original_sale.items.all()
        fully_returned = all(
            si.quantity_returned >= si.quantity for si in all_items
        )
        partially_returned = any(
            si.quantity_returned > 0 for si in all_items
        )

        if fully_returned:
            original_sale.status = 'fully_returned'
        elif partially_returned:
            original_sale.status = 'partially_returned'

        original_sale.save(update_fields=['status', 'updated_at'])

        return sale_return
