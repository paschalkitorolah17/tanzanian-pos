from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal

from apps.accounts.decorators import role_required
from apps.sales.models import Sale, SaleItem
from apps.sales.services import ReturnService
from apps.payments.models import PaymentMethod


@role_required('business_owner', 'manager', 'cashier')
def process_return(request, sale_id):
    business = request.user.business
    sale = get_object_or_404(
        Sale.objects.prefetch_related('items__product'),
        pk=sale_id,
        business=business
    )

    if sale.status in ['cancelled', 'fully_returned']:
        messages.error(request, 'This sale cannot be returned.')
        return redirect('sale-detail', pk=sale.id)

    # Cashiers can only return their own sales
    if request.user.role == 'cashier' and sale.cashier != request.user:
        messages.error(request, 'You can only return your own sales.')
        return redirect('sales-history')

    payment_methods = PaymentMethod.objects.filter(business=business, is_active=True)

    if request.method == 'POST':
        try:
            items = []
            for item in sale.items.all():
                qty_key = f'qty_{item.id}'
                qty_str = request.POST.get(qty_key, '0').strip()
                if qty_str:
                    qty = Decimal(qty_str)
                    if qty > 0:
                        items.append({
                            'sale_item_id': item.id,
                            'quantity': str(qty)
                        })

            if not items:
                raise ValueError('Select at least one item to return')

            reason = request.POST.get('reason', '').strip()
            refund_method_id = request.POST.get('refund_method') or None
            refund_reference = request.POST.get('refund_reference', '').strip()

            refund_method = None
            if refund_method_id:
                refund_method = PaymentMethod.objects.get(
                    id=refund_method_id, business=business
                )

            ret = ReturnService.create_return(
                original_sale=sale,
                items=items,
                processed_by=request.user,
                reason=reason,
                refund_method=refund_method,
                refund_reference=refund_reference,
            )

            messages.success(
                request,
                f'Return {ret.return_number} created. Refund amount: TZS {ret.refund_amount}'
            )
            return redirect('sale-detail', pk=sale.id)

        except Exception as e:
            messages.error(request, str(e))

    # Prepare returnable items
    returnable_items = []
    for item in sale.items.all():
        remaining = item.quantity - item.quantity_returned
        if remaining > 0:
            returnable_items.append({
                'item': item,
                'remaining': remaining,
            })

    return render(request, 'sales/process_return.html', {
        'sale': sale,
        'returnable_items': returnable_items,
        'payment_methods': payment_methods,
    })
