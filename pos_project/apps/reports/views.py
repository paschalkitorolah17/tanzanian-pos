from django.shortcuts import render, redirect
from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import json

from apps.accounts.decorators import leadership_required
from apps.sales.models import Sale, SaleItem
from apps.inventory.models import StockLevel
from apps.businesses.branch_utils import get_current_branch


@leadership_required
def dashboard(request):
    business = getattr(request.user, 'business', None)
    current_branch = get_current_branch(request)

    context = {
        'business': business,
        'current_branch': current_branch,
        'today_total': Decimal('0.00'),
        'today_count': 0,
        'today_profit': Decimal('0.00'),
        'low_stock': [],
        'recent_sales': [],
        'top_products': [],
        'chart_labels': '[]',
        'chart_values': '[]',
        'error': None,
    }

    if not business:
        context['error'] = 'No business is assigned to your account.'
        return render(request, 'reports/dashboard.html', context)

    now = timezone.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    # Base sale filter
    sale_filter = {
        'business': business,
        'status': 'completed',
        'created_at__gte': start_of_day,
        'created_at__lt': end_of_day,
    }
    if current_branch:
        sale_filter['branch'] = current_branch

    today_sales_qs = Sale.objects.filter(**sale_filter)

    context['today_count'] = today_sales_qs.count()
    context['today_total'] = today_sales_qs.aggregate(
        total=Coalesce(Sum('grand_total'), Decimal('0.00'))
    )['total']

    # Profit filter
    profit_filter = {
        'sale__business': business,
        'sale__status': 'completed',
        'sale__created_at__gte': start_of_day,
        'sale__created_at__lt': end_of_day,
    }
    if current_branch:
        profit_filter['sale__branch'] = current_branch

    profit = SaleItem.objects.filter(**profit_filter).aggregate(
        profit=Coalesce(
            Sum(
                (F('unit_price') - F('cost_price_at_sale')) * F('quantity') - F('discount'),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            Decimal('0.00')
        )
    )['profit']
    context['today_profit'] = profit or Decimal('0.00')

    # Low stock
    stock_qs = StockLevel.objects.filter(
        product__business=business,
        product__is_active=True,
        quantity__lte=F('product__reorder_level')
    ).select_related('product')
    if current_branch:
        stock_qs = stock_qs.filter(branch=current_branch)
    context['low_stock'] = list(stock_qs[:8])

    # Recent sales
    recent_qs = Sale.objects.filter(business=business, status='completed')
    if current_branch:
        recent_qs = recent_qs.filter(branch=current_branch)
    context['recent_sales'] = list(
        recent_qs.select_related('cashier', 'branch').order_by('-created_at')[:8]
    )

    # Top products today
    top_filter = {
        'sale__business': business,
        'sale__status': 'completed',
        'sale__created_at__gte': start_of_day,
        'sale__created_at__lt': end_of_day,
    }
    if current_branch:
        top_filter['sale__branch'] = current_branch

    context['top_products'] = list(
        SaleItem.objects.filter(**top_filter)
        .values('product__name')
        .annotate(total_qty=Sum('quantity'), total_sales=Sum('line_total'))
        .order_by('-total_qty')[:5]
    )

    # Last 7 days chart (timezone-safe + branch aware)
    labels = []
    values = []

    for i in range(6, -1, -1):
        day = timezone.localdate() - timedelta(days=i)
        labels.append(day.strftime('%d %b'))

        day_start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        day_end = day_start + timedelta(days=1)

        day_filter = {
            'business': business,
            'status': 'completed',
            'created_at__gte': day_start,
            'created_at__lt': day_end,
        }
        if current_branch:
            day_filter['branch'] = current_branch

        total = Sale.objects.filter(**day_filter).aggregate(
            total=Coalesce(Sum('grand_total'), Decimal('0.00'))
        )['total']

        values.append(float(total))

    context['chart_labels'] = json.dumps(labels)
    context['chart_values'] = json.dumps(values)

    return render(request, 'reports/dashboard.html', context)


@leadership_required
def sales_report(request):
    business = request.user.business
    current_branch = get_current_branch(request)

    if not business:
        return render(request, 'reports/sales_report.html', {'error': 'No business assigned'})

    today = timezone.localdate()
    date_from = request.GET.get('from', (today - timedelta(days=7)).isoformat())
    date_to = request.GET.get('to', today.isoformat())

    try:
        start = datetime.strptime(date_from, '%Y-%m-%d').date()
        end = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        start = today - timedelta(days=7)
        end = today

    start_dt = timezone.make_aware(datetime.combine(start, datetime.min.time()))
    end_dt = timezone.make_aware(datetime.combine(end + timedelta(days=1), datetime.min.time()))

    sales = Sale.objects.filter(
        business=business,
        status='completed',
        created_at__gte=start_dt,
        created_at__lt=end_dt
    )
    if current_branch:
        sales = sales.filter(branch=current_branch)

    summary = sales.aggregate(
        total_sales=Coalesce(Sum('grand_total'), Decimal('0.00')),
        total_transactions=Count('id'),
        total_tax=Coalesce(Sum('tax_total'), Decimal('0.00')),
        total_discount=Coalesce(Sum('discount_total'), Decimal('0.00')),
    )

    by_cashier = list(
        sales.values('cashier__username', 'cashier__first_name', 'cashier__last_name')
             .annotate(total=Sum('grand_total'), count=Count('id'))
             .order_by('-total')
    )

    by_day = list(
        sales.annotate(day=TruncDate('created_at'))
             .values('day')
             .annotate(total=Sum('grand_total'), count=Count('id'))
             .order_by('day')
    )

    item_filter = {
        'sale__business': business,
        'sale__status': 'completed',
        'sale__created_at__gte': start_dt,
        'sale__created_at__lt': end_dt,
    }
    if current_branch:
        item_filter['sale__branch'] = current_branch

    top_products = list(
        SaleItem.objects.filter(**item_filter)
        .values('product__name')
        .annotate(total_qty=Sum('quantity'), total_sales=Sum('line_total'))
        .order_by('-total_sales')[:10]
    )

    context = {
        'business': business,
        'current_branch': current_branch,
        'date_from': start.isoformat(),
        'date_to': end.isoformat(),
        'summary': summary,
        'by_cashier': by_cashier,
        'by_day': by_day,
        'top_products': top_products,
        'sales': sales.select_related('cashier', 'branch').order_by('-created_at')[:50],
    }
    return render(request, 'reports/sales_report.html', context)


@leadership_required
def sales_report_csv(request):
    import csv
    from django.http import HttpResponse

    business = request.user.business
    current_branch = get_current_branch(request)

    if not business:
        return redirect('sales-report')

    today = timezone.localdate()
    date_from = request.GET.get('from', (today - timedelta(days=7)).isoformat())
    date_to = request.GET.get('to', today.isoformat())

    try:
        start = datetime.strptime(date_from, '%Y-%m-%d').date()
        end = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        start = today - timedelta(days=7)
        end = today

    start_dt = timezone.make_aware(datetime.combine(start, datetime.min.time()))
    end_dt = timezone.make_aware(datetime.combine(end + timedelta(days=1), datetime.min.time()))

    sales = Sale.objects.filter(
        business=business,
        status='completed',
        created_at__gte=start_dt,
        created_at__lt=end_dt
    ).select_related('cashier', 'branch').order_by('-created_at')

    if current_branch:
        sales = sales.filter(branch=current_branch)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_{date_from}_to_{date_to}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Receipt', 'Date', 'Time', 'Cashier', 'Branch',
        'Subtotal', 'Discount', 'Tax', 'Grand Total', 'Status'
    ])

    for s in sales:
        writer.writerow([
            s.transaction_number,
            s.created_at.strftime('%Y-%m-%d'),
            s.created_at.strftime('%H:%M'),
            s.cashier.get_full_name() or s.cashier.username,
            s.branch.name,
            s.subtotal,
            s.discount_total,
            s.tax_total,
            s.grand_total,
            s.status,
        ])

    return response


@leadership_required
def profit_loss_report(request):
    """
    Simple Profit & Loss for a date range.
    Revenue = completed sales
    COGS ≈ sum of (cost_price_at_sale * quantity)
    Gross Profit = Revenue - COGS
    Expenses = recorded expenses in the same period
    Net Profit ≈ Gross Profit - Expenses
    """
    business = request.user.business
    current_branch = get_current_branch(request)

    if not business:
        return render(request, 'reports/profit_loss.html', {'error': 'No business assigned'})

    today = timezone.localdate()
    date_from = request.GET.get('from', (today.replace(day=1)).isoformat())
    date_to = request.GET.get('to', today.isoformat())

    try:
        start = datetime.strptime(date_from, '%Y-%m-%d').date()
        end = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        start = today.replace(day=1)
        end = today

    start_dt = timezone.make_aware(datetime.combine(start, datetime.min.time()))
    end_dt = timezone.make_aware(datetime.combine(end + timedelta(days=1), datetime.min.time()))

    # Sales
    sales_qs = Sale.objects.filter(
        business=business,
        status='completed',
        created_at__gte=start_dt,
        created_at__lt=end_dt
    )
    if current_branch:
        sales_qs = sales_qs.filter(branch=current_branch)

    revenue = sales_qs.aggregate(
        total=Coalesce(Sum('grand_total'), Decimal('0.00'))
    )['total']

    # Cost of Goods Sold
    item_filter = {
        'sale__business': business,
        'sale__status': 'completed',
        'sale__created_at__gte': start_dt,
        'sale__created_at__lt': end_dt,
    }
    if current_branch:
        item_filter['sale__branch'] = current_branch

    cogs = SaleItem.objects.filter(**item_filter).aggregate(
        total=Coalesce(
            Sum(F('cost_price_at_sale') * F('quantity'),
                output_field=DecimalField(max_digits=14, decimal_places=2)),
            Decimal('0.00')
        )
    )['total']

    gross_profit = revenue - cogs

    # Expenses
    from apps.expenses.models import Expense
    expense_qs = Expense.objects.filter(
        business=business,
        date__gte=start,
        date__lte=end
    )
    if current_branch:
        expense_qs = expense_qs.filter(branch=current_branch)

    total_expenses = expense_qs.aggregate(
        total=Coalesce(Sum('amount'), Decimal('0.00'))
    )['total']

    # Expense breakdown by category
    expense_by_category = list(
        expense_qs.values('category__name')
                  .annotate(total=Sum('amount'))
                  .order_by('-total')
    )

    net_profit = gross_profit - total_expenses

    context = {
        'business': business,
        'current_branch': current_branch,
        'date_from': start.isoformat(),
        'date_to': end.isoformat(),
        'revenue': revenue,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'total_expenses': total_expenses,
        'expense_by_category': expense_by_category,
        'net_profit': net_profit,
    }
    return render(request, 'reports/profit_loss.html', context)


@leadership_required
def expense_report(request):
    """Expense summary by category for a date range."""
    from apps.expenses.models import Expense

    business = request.user.business
    current_branch = get_current_branch(request)

    if not business:
        return render(request, 'reports/expense_report.html', {'error': 'No business assigned'})

    today = timezone.localdate()
    date_from = request.GET.get('from', (today.replace(day=1)).isoformat())
    date_to = request.GET.get('to', today.isoformat())

    try:
        start = datetime.strptime(date_from, '%Y-%m-%d').date()
        end = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        start = today.replace(day=1)
        end = today

    expenses = Expense.objects.filter(
        business=business,
        date__gte=start,
        date__lte=end
    ).select_related('category', 'branch', 'payment_method')

    if current_branch:
        expenses = expenses.filter(branch=current_branch)

    total = expenses.aggregate(
        total=Coalesce(Sum('amount'), Decimal('0.00'))
    )['total']

    by_category = list(
        expenses.values('category__name')
                .annotate(total=Sum('amount'), count=Count('id'))
                .order_by('-total')
    )

    context = {
        'business': business,
        'current_branch': current_branch,
        'date_from': start.isoformat(),
        'date_to': end.isoformat(),
        'total': total,
        'by_category': by_category,
        'expenses': expenses.order_by('-date')[:100],
    }
    return render(request, 'reports/expense_report.html', context)


@leadership_required
def profit_loss_report(request):
    """
    Simple Profit & Loss for a date range.
    Revenue = completed sales
    COGS ≈ sum of (cost_price_at_sale * quantity)
    Gross Profit = Revenue - COGS
    Expenses = recorded expenses in the same period
    Net Profit ≈ Gross Profit - Expenses
    """
    business = request.user.business
    current_branch = get_current_branch(request)

    if not business:
        return render(request, 'reports/profit_loss.html', {'error': 'No business assigned'})

    today = timezone.localdate()
    date_from = request.GET.get('from', (today.replace(day=1)).isoformat())
    date_to = request.GET.get('to', today.isoformat())

    try:
        start = datetime.strptime(date_from, '%Y-%m-%d').date()
        end = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        start = today.replace(day=1)
        end = today

    start_dt = timezone.make_aware(datetime.combine(start, datetime.min.time()))
    end_dt = timezone.make_aware(datetime.combine(end + timedelta(days=1), datetime.min.time()))

    # Sales
    sales_qs = Sale.objects.filter(
        business=business,
        status='completed',
        created_at__gte=start_dt,
        created_at__lt=end_dt
    )
    if current_branch:
        sales_qs = sales_qs.filter(branch=current_branch)

    revenue = sales_qs.aggregate(
        total=Coalesce(Sum('grand_total'), Decimal('0.00'))
    )['total']

    # Cost of Goods Sold
    item_filter = {
        'sale__business': business,
        'sale__status': 'completed',
        'sale__created_at__gte': start_dt,
        'sale__created_at__lt': end_dt,
    }
    if current_branch:
        item_filter['sale__branch'] = current_branch

    cogs = SaleItem.objects.filter(**item_filter).aggregate(
        total=Coalesce(
            Sum(F('cost_price_at_sale') * F('quantity'),
                output_field=DecimalField(max_digits=14, decimal_places=2)),
            Decimal('0.00')
        )
    )['total']

    gross_profit = revenue - cogs

    # Expenses
    from apps.expenses.models import Expense
    expense_qs = Expense.objects.filter(
        business=business,
        date__gte=start,
        date__lte=end
    )
    if current_branch:
        expense_qs = expense_qs.filter(branch=current_branch)

    total_expenses = expense_qs.aggregate(
        total=Coalesce(Sum('amount'), Decimal('0.00'))
    )['total']

    # Expense breakdown by category
    expense_by_category = list(
        expense_qs.values('category__name')
                  .annotate(total=Sum('amount'))
                  .order_by('-total')
    )

    net_profit = gross_profit - total_expenses

    context = {
        'business': business,
        'current_branch': current_branch,
        'date_from': start.isoformat(),
        'date_to': end.isoformat(),
        'revenue': revenue,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'total_expenses': total_expenses,
        'expense_by_category': expense_by_category,
        'net_profit': net_profit,
    }
    return render(request, 'reports/profit_loss.html', context)


@leadership_required
def expense_report(request):
    """Expense summary by category for a date range."""
    from apps.expenses.models import Expense

    business = request.user.business
    current_branch = get_current_branch(request)

    if not business:
        return render(request, 'reports/expense_report.html', {'error': 'No business assigned'})

    today = timezone.localdate()
    date_from = request.GET.get('from', (today.replace(day=1)).isoformat())
    date_to = request.GET.get('to', today.isoformat())

    try:
        start = datetime.strptime(date_from, '%Y-%m-%d').date()
        end = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        start = today.replace(day=1)
        end = today

    expenses = Expense.objects.filter(
        business=business,
        date__gte=start,
        date__lte=end
    ).select_related('category', 'branch', 'payment_method')

    if current_branch:
        expenses = expenses.filter(branch=current_branch)

    total = expenses.aggregate(
        total=Coalesce(Sum('amount'), Decimal('0.00'))
    )['total']

    by_category = list(
        expenses.values('category__name')
                .annotate(total=Sum('amount'), count=Count('id'))
                .order_by('-total')
    )

    context = {
        'business': business,
        'current_branch': current_branch,
        'date_from': start.isoformat(),
        'date_to': end.isoformat(),
        'total': total,
        'by_category': by_category,
        'expenses': expenses.order_by('-date')[:100],
    }
    return render(request, 'reports/expense_report.html', context)
