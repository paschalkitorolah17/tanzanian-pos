from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta, datetime

from apps.accounts.decorators import role_required
from apps.sales.models import Sale


@role_required('business_owner', 'manager', 'accountant', 'auditor', 'cashier', 'sales_associate')
def sales_history(request):
    business = request.user.business
    sales = Sale.objects.filter(
        business=business
    ).select_related('cashier', 'branch', 'customer').order_by('-created_at')

    # Optional filters
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')

    if q:
        sales = sales.filter(transaction_number__icontains=q)

    if status:
        sales = sales.filter(status=status)

    if date_from:
        try:
            start = datetime.strptime(date_from, '%Y-%m-%d').date()
            start_dt = timezone.make_aware(datetime.combine(start, datetime.min.time()))
            sales = sales.filter(created_at__gte=start_dt)
        except ValueError:
            pass

    if date_to:
        try:
            end = datetime.strptime(date_to, '%Y-%m-%d').date()
            end_dt = timezone.make_aware(datetime.combine(end + timedelta(days=1), datetime.min.time()))
            sales = sales.filter(created_at__lt=end_dt)
        except ValueError:
            pass

    # Cashiers only see their own sales (optional business rule)
    if request.user.role in ['cashier', 'sales_associate']:
        sales = sales.filter(cashier=request.user)

    paginator = Paginator(sales, 25)
    page = request.GET.get('page')
    sales_page = paginator.get_page(page)

    return render(request, 'sales/history.html', {
        'sales': sales_page,
        'q': q,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
        'business': business,
    })


@role_required('business_owner', 'manager', 'accountant', 'auditor', 'cashier', 'sales_associate')
def sale_detail(request, pk):
    business = request.user.business
    sale = get_object_or_404(
        Sale.objects.select_related('cashier', 'branch', 'customer')
                    .prefetch_related('items__product', 'payments__payment_method'),
        pk=pk,
        business=business
    )

    # Cashiers can only view their own sales
    if request.user.role in ['cashier', 'sales_associate'] and sale.cashier != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    return render(request, 'sales/detail.html', {
        'sale': sale,
    })
