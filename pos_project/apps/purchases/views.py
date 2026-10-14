from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal, InvalidOperation

from apps.accounts.decorators import leadership_required
from apps.purchases.services import PurchaseService
from apps.purchases.models import Purchase
from apps.products.models import Product
from apps.suppliers.models import Supplier
from apps.businesses.models import Branch


@leadership_required
def purchase_list(request):
    business = request.user.business
    purchases = Purchase.objects.filter(
        business=business
    ).select_related('supplier', 'branch', 'received_by').order_by('-created_at')[:50]

    return render(request, 'purchases/list.html', {
        'purchases': purchases,
        'business': business,
    })


@leadership_required
def receive_stock(request):
    business = request.user.business
    if not business:
        messages.error(request, 'No business assigned')
        return redirect('purchase-list')

    products = Product.objects.filter(business=business, is_active=True).order_by('name')
    suppliers = Supplier.objects.filter(business=business, is_active=True)
    branches = Branch.objects.filter(business=business, is_active=True)

    if request.method == 'POST':
        try:
            branch_id = request.POST.get('branch')
            supplier_id = request.POST.get('supplier') or None
            reference = request.POST.get('reference', '').strip()
            notes = request.POST.get('notes', '').strip()

            branch = Branch.objects.get(id=branch_id, business=business)

            # Collect items from form (we support multiple rows)
            product_ids = request.POST.getlist('product_id')
            quantities = request.POST.getlist('quantity')
            unit_costs = request.POST.getlist('unit_cost')

            items = []
            for pid, qty, cost in zip(product_ids, quantities, unit_costs):
                if pid and qty:
                    items.append({
                        'product_id': int(pid),
                        'quantity': qty,
                        'unit_cost': cost or '0'
                    })

            if not items:
                raise ValueError('Add at least one product')

            supplier = None
            if supplier_id:
                supplier = Supplier.objects.get(id=supplier_id, business=business)

            purchase = PurchaseService.receive_stock(
                branch=branch,
                received_by=request.user,
                items=items,
                supplier=supplier,
                reference=reference,
                notes=notes,
            )

            messages.success(
                request,
                f'Stock received successfully. Total cost: TZS {purchase.total_cost}'
            )
            return redirect('purchase-list')

        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'purchases/receive.html', {
        'products': products,
        'suppliers': suppliers,
        'branches': branches,
    })
