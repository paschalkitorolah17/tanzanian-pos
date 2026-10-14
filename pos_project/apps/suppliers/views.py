from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from apps.accounts.decorators import role_required
from apps.suppliers.models import Supplier


@role_required('business_owner', 'manager', 'operator')
def supplier_list(request):
    business = request.user.business
    suppliers = Supplier.objects.filter(business=business).order_by('name')

    q = request.GET.get('q', '').strip()
    if q:
        suppliers = suppliers.filter(name__icontains=q) | suppliers.filter(phone__icontains=q)

    return render(request, 'suppliers/list.html', {
        'suppliers': suppliers,
        'q': q,
        'business': business,
    })


@role_required('business_owner', 'manager', 'operator')
def supplier_create(request):
    business = request.user.business

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not name:
            messages.error(request, 'Supplier name is required')
        elif Supplier.objects.filter(business=business, name=name).exists():
            messages.error(request, f'Supplier "{name}" already exists')
        else:
            Supplier.objects.create(
                business=business,
                name=name,
                phone=phone,
                email=email,
                address=address,
                notes=notes,
            )
            messages.success(request, f'Supplier "{name}" created.')
            return redirect('supplier-list')

    return render(request, 'suppliers/form.html', {
        'title': 'Add Supplier',
        'supplier': None,
    })


@role_required('business_owner', 'manager', 'operator')
def supplier_edit(request, pk):
    business = request.user.business
    supplier = get_object_or_404(Supplier, pk=pk, business=business)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        notes = request.POST.get('notes', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if not name:
            messages.error(request, 'Supplier name is required')
        elif Supplier.objects.filter(business=business, name=name).exclude(pk=pk).exists():
            messages.error(request, f'Supplier "{name}" already exists')
        else:
            supplier.name = name
            supplier.phone = phone
            supplier.email = email
            supplier.address = address
            supplier.notes = notes
            supplier.is_active = is_active
            supplier.save()
            messages.success(request, f'Supplier "{name}" updated.')
            return redirect('supplier-list')

    return render(request, 'suppliers/form.html', {
        'title': 'Edit Supplier',
        'supplier': supplier,
    })
