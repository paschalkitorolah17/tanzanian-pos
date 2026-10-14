"""
SALE SERVICE
============

Atomic sale creation with stock reduction and payments.
"""

from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.sales.models import Sale, SaleItem
from apps.payments.models import Payment, PaymentMethod
from apps.inventory.services import StockService
from apps.inventory.models import Warehouse
from apps.products.models import Product


class SaleService:

    @staticmethod
    def _generate_transaction_number(branch) -> str:
        today = timezone.localdate()
        prefix = f"SALE-{today.strftime('%Y%m%d')}"

        last_sale = Sale.objects.filter(
            business=branch.business,
            transaction_number__startswith=prefix
        ).order_by('-transaction_number').first()

        if last_sale:
            try:
                last_seq = int(last_sale.transaction_number.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1

        return f"{prefix}-{next_seq:06d}"

    @staticmethod
    def _calculate_line(product, quantity: Decimal, discount: Decimal = Decimal('0')):
        if quantity <= 0:
            raise ValidationError(f"Quantity for {product.name} must be positive.")

        price = product.selling_price

        if discount < 0:
            raise ValidationError("Discount cannot be negative.")
        if discount > price * quantity:
            raise ValidationError(f"Discount too high for {product.name}.")

        line_subtotal = (price * quantity) - discount

        if product.tax_status == 'taxable':
            tax_rate = product.tax_rate / Decimal('100')
            tax_amount = (line_subtotal * tax_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            tax_amount = Decimal('0.00')

        line_total = line_subtotal + tax_amount

        return {
            'unit_price': price,
            'discount': discount,
            'tax_amount': tax_amount,
            'line_total': line_total,
            'cost_price_at_sale': product.cost_price,
        }

    @staticmethod
    @transaction.atomic
    def create_sale(
        *,
        branch,
        cashier,
        items: list,
        payments: list,
        customer=None,
        notes: str = '',
        idempotency_key: str = None,
    ) -> Sale:
        """
        Create a complete sale with payments and stock reduction.

        items = [
            {'product_id': 1, 'quantity': '2', 'discount': '0'},
            ...
        ]
        payments = [
            {'payment_method_id': 1, 'amount': '5000', 'reference': ''},
            {'payment_method_id': 2, 'amount': '3000', 'reference': 'QK12ABC'},
        ]
        """

        # 1. Idempotency check
        if idempotency_key:
            existing = Sale.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                return existing

        if not items:
            raise ValidationError("Cart is empty.")
        if not payments:
            raise ValidationError("At least one payment is required.")

        # 2. Load products
        product_ids = [item['product_id'] for item in items]
        products = {
            p.id: p for p in Product.objects.filter(
                id__in=product_ids,
                business=branch.business,
                is_active=True
            )
        }
        if len(products) != len(set(product_ids)):
            raise ValidationError("One or more products are invalid or inactive.")

        # 3. Calculate totals (server-side)
        calculated_items = []
        subtotal = Decimal('0.00')
        discount_total = Decimal('0.00')
        tax_total = Decimal('0.00')

        for item in items:
            product = products[item['product_id']]
            qty = Decimal(str(item['quantity']))
            discount = Decimal(str(item.get('discount', 0)))

            line = SaleService._calculate_line(product, qty, discount)

            calculated_items.append({
                'product': product,
                'quantity': qty,
                **line
            })

            subtotal += (line['unit_price'] * qty)
            discount_total += discount
            tax_total += line['tax_amount']

        grand_total = (subtotal - discount_total + tax_total).quantize(Decimal('0.01'))

        # 4. Validate payments sum
        payment_total = sum(Decimal(str(p['amount'])) for p in payments)
        if payment_total != grand_total:
            raise ValidationError(
                f"Payment total ({payment_total}) does not match sale total ({grand_total})."
            )

        # 5. Create Sale header
        sale = Sale.objects.create(
            business=branch.business,
            branch=branch,
            transaction_number=SaleService._generate_transaction_number(branch),
            customer=customer,
            cashier=cashier,
            subtotal=subtotal.quantize(Decimal('0.01')),
            discount_total=discount_total.quantize(Decimal('0.01')),
            tax_total=tax_total.quantize(Decimal('0.01')),
            grand_total=grand_total,
            notes=notes,
            idempotency_key=idempotency_key,
            status='completed',
        )

        # 6. Get default warehouse once
        warehouse = Warehouse.objects.filter(
            branch=branch,
            is_default=True,
            is_active=True
        ).first()

        # 7. Create SaleItems + reduce stock
        for item in calculated_items:
            SaleItem.objects.create(
                sale=sale,
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                discount=item['discount'],
                tax_amount=item['tax_amount'],
                line_total=item['line_total'],
                cost_price_at_sale=item['cost_price_at_sale'],
            )

            # Reduce stock using the default warehouse
            StockService.adjust_stock(
                product=item['product'],
                branch=branch,
                quantity=-item['quantity'],
                transaction_type='sale',
                user=cashier,
                warehouse=warehouse,
                reference_type='sale',
                reference_id=sale.id,
                reason=f'Sale {sale.transaction_number}',
            )

        # 8. Create payments
        for p in payments:
            method = PaymentMethod.objects.get(
                id=p['payment_method_id'],
                business=branch.business,
                is_active=True
            )
            Payment.objects.create(
                sale=sale,
                payment_method=method,
                amount=Decimal(str(p['amount'])),
                reference=p.get('reference', ''),
                received_by=cashier,
            )

        return sale
