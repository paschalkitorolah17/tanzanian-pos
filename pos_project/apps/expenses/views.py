from django.shortcuts import render, redirect
from django.db import models
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal, InvalidOperation

from apps.accounts.decorators import leadership_required
from apps.expenses.models import Expense, ExpenseCategory
from apps.payments.models import PaymentMethod
from apps.businesses.models import Branch


@leadership_required
def expense_list(request):
    business = request.user.business
    if not business:
        return render(request, 'expenses/list.html', {'error': 'No business assigned'})

    expenses = Expense.objects.filter(
        business=business
    ).select_related(
        'category', 'branch', 'payment_method', 'recorded_by'
    ).order_by('-date', '-created_at')[:100]

    # Simple totals for current month
    today = timezone.localdate()
    month_start = today.replace(day=1)
    month_total = Expense.objects.filter(
        business=business,
        date__gte=month_start,
        date__lte=today
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    context = {
        'expenses': expenses,
        'month_total': month_total,
        'business': business,
    }
    return render(request, 'expenses/list.html', context)


@leadership_required
def expense_create(request):
    business = request.user.business
    if not business:
        messages.error(request, 'No business assigned')
        return redirect('expense-list')

    categories = ExpenseCategory.objects.filter(business=business, is_active=True)
    branches = Branch.objects.filter(business=business, is_active=True)
    payment_methods = PaymentMethod.objects.filter(business=business, is_active=True)

    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            amount = Decimal(request.POST.get('amount', '0'))
            date = request.POST.get('date')
            description = request.POST.get('description', '').strip()
            reference = request.POST.get('reference', '').strip()
            branch_id = request.POST.get('branch') or None
            payment_method_id = request.POST.get('payment_method') or None

            if amount <= 0:
                raise ValueError('Amount must be greater than zero')

            category = ExpenseCategory.objects.get(id=category_id, business=business)

            expense = Expense(
                business=business,
                category=category,
                amount=amount,
                date=date,
                description=description,
                reference=reference,
                recorded_by=request.user,
            )

            if branch_id:
                expense.branch = Branch.objects.get(id=branch_id, business=business)
            if payment_method_id:
                expense.payment_method = PaymentMethod.objects.get(
                    id=payment_method_id, business=business
                )

            expense.save()
            messages.success(request, f'Expense of TZS {amount} recorded successfully.')
            return redirect('expense-list')

        except (InvalidOperation, ValueError) as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {e}')

    context = {
        'categories': categories,
        'branches': branches,
        'payment_methods': payment_methods,
        'today': timezone.localdate().isoformat(),
    }
    return render(request, 'expenses/create.html', context)


@leadership_required
def expense_csv(request):
    """Export expenses as CSV."""
    import csv
    from django.http import HttpResponse
    from django.utils import timezone
    from datetime import timedelta

    business = request.user.business
    if not business:
        return redirect('expense-list')

    expenses = Expense.objects.filter(
        business=business
    ).select_related('category', 'branch', 'payment_method', 'recorded_by').order_by('-date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="expenses_{timezone.localdate()}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Category', 'Description', 'Branch',
        'Payment Method', 'Amount (TZS)', 'Reference', 'Recorded By'
    ])

    for e in expenses:
        writer.writerow([
            e.date.isoformat(),
            e.category.name,
            e.description,
            e.branch.name if e.branch else '',
            e.payment_method.name if e.payment_method else '',
            e.amount,
            e.reference,
            e.recorded_by.username,
        ])

    return response
