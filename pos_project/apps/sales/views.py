from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from .models import Sale


@login_required
def sale_receipt(request, sale_id):
    """
    Display a printable receipt for a completed sale.
    Only the owner business can view it.
    """
    sale = get_object_or_404(
        Sale.objects.select_related(
            'business', 'branch', 'cashier', 'customer'
        ).prefetch_related(
            'items__product', 'payments__payment_method'
        ),
        id=sale_id,
        business=request.user.business
    )
    return render(request, 'pos/receipt.html', {'sale': sale})
