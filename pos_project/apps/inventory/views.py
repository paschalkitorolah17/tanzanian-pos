from django.shortcuts import render
from django.db.models import F, Q

from apps.accounts.decorators import role_required
from apps.inventory.models import StockLevel, InventoryTransaction
from apps.businesses.branch_utils import get_current_branch


@role_required('business_owner', 'manager', 'operator')
def stock_list(request):
    business = request.user.business
    current_branch = get_current_branch(request)

    stocks = StockLevel.objects.filter(
        product__business=business,
        product__is_active=True
    ).select_related('product', 'branch', 'warehouse')

    if current_branch:
        stocks = stocks.filter(branch=current_branch)

    stocks = stocks.order_by('product__name')

    q = request.GET.get('q', '').strip()
    low_only = request.GET.get('low') == '1'

    if q:
        stocks = stocks.filter(
            Q(product__name__icontains=q) | Q(product__sku__icontains=q)
        )

    if low_only:
        stocks = stocks.filter(quantity__lte=F('product__reorder_level'))

    return render(request, 'inventory/stock_list.html', {
        'stocks': stocks,
        'q': q,
        'low_only': low_only,
        'business': business,
        'current_branch': current_branch,
    })


@role_required('business_owner', 'manager', 'operator', 'auditor')
def stock_movements(request):
    business = request.user.business
    current_branch = get_current_branch(request)

    movements = InventoryTransaction.objects.filter(
        product__business=business
    ).select_related('product', 'branch', 'created_by')

    if current_branch:
        movements = movements.filter(branch=current_branch)

    movements = movements.order_by('-created_at')[:100]

    return render(request, 'inventory/movements.html', {
        'movements': movements,
        'business': business,
        'current_branch': current_branch,
    })
