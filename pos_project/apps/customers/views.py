from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from apps.accounts.decorators import role_required
from apps.customers.models import Customer


@role_required('business_owner', 'manager', 'cashier', 'sales_associate', 'accountant')
def customer_list(request):
    business = request.user.business
    customers = Customer.objects.filter(business=business).order_by('name')

    q = request.GET.get('q', '').strip()
    if q:
        customers = customers.filter(name__icontains=q) | customers.filter(phone__icontains=q)

    return render(request, 'customers/list.html', {
        'customers': customers,
        'q': q,
        'business': business,
    })


@role_required('business_owner', 'manager', 'cashier', 'sales_associate')
def customer_create(request):
    business = request.user.business

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()

        if not name:
            messages.error(request, 'Customer name is required')
        else:
            # Optional: prevent duplicate phone
            if phone and Customer.objects.filter(business=business, phone=phone).exists():
                messages.error(request, f'Phone "{phone}" already exists')
            else:
                Customer.objects.create(
                    business=business,
                    name=name,
                    phone=phone,
                    email=email,
                    address=address,
                )
                messages.success(request, f'Customer "{name}" created.')
                return redirect('customer-list')

    return render(request, 'customers/form.html', {
        'title': 'Add Customer',
        'customer': None,
    })


@role_required('business_owner', 'manager', 'cashier', 'sales_associate')
def customer_edit(request, pk):
    business = request.user.business
    customer = get_object_or_404(Customer, pk=pk, business=business)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if not name:
            messages.error(request, 'Customer name is required')
        else:
            if phone and Customer.objects.filter(business=business, phone=phone).exclude(pk=pk).exists():
                messages.error(request, f'Phone "{phone}" already exists')
            else:
                customer.name = name
                customer.phone = phone
                customer.email = email
                customer.address = address
                customer.is_active = is_active
                customer.save()
                messages.success(request, f'Customer "{name}" updated.')
                return redirect('customer-list')

    return render(request, 'customers/form.html', {
        'title': 'Edit Customer',
        'customer': customer,
    })
