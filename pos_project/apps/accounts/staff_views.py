from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model

from apps.accounts.decorators import role_required
from apps.accounts.models import User

UserModel = get_user_model()


@role_required('business_owner', 'manager')
def staff_list(request):
    business = request.user.business
    users = UserModel.objects.filter(
        business=business
    ).order_by('role', 'username')

    return render(request, 'accounts/staff_list.html', {
        'users': users,
        'business': business,
    })


@role_required('business_owner', 'manager')
def staff_create(request):
    business = request.user.business
    if not business:
        messages.error(request, 'No business assigned')
        return redirect('staff-list')

    # Roles that a manager/owner is allowed to create
    allowed_roles = [
        ('cashier', 'Cashier'),
        ('sales_associate', 'Sales Associate'),
        ('operator', 'Operator'),
        ('manager', 'Manager'),
        ('accountant', 'Accountant'),
    ]

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        role = request.POST.get('role')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if not username or not password:
            messages.error(request, 'Username and password are required')
        elif password != password2:
            messages.error(request, 'Passwords do not match')
        elif UserModel.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
        elif role not in dict(allowed_roles):
            messages.error(request, 'Invalid role')
        else:
            user = UserModel.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=role,
                business=business,
                is_staff=False,
            )
            messages.success(request, f'User “{username}” created successfully as {user.get_role_display()}.')
            return redirect('staff-list')

    return render(request, 'accounts/staff_create.html', {
        'allowed_roles': allowed_roles,
    })
