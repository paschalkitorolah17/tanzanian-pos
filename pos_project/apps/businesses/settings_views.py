from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import default_storage

from apps.accounts.decorators import role_required
from apps.businesses.models import Business


@role_required('business_owner', 'manager')
def business_settings(request):
    business = request.user.business
    if not business:
        messages.error(request, 'No business assigned')
        return redirect('dashboard')

    if request.method == 'POST':
        business.name = request.POST.get('name', '').strip() or business.name
        business.tin = request.POST.get('tin', '').strip()
        business.phone = request.POST.get('phone', '').strip()
        business.email = request.POST.get('email', '').strip()
        business.address = request.POST.get('address', '').strip()
        business.receipt_footer = request.POST.get('receipt_footer', '').strip()

        # Optional VRN if the field exists
        if hasattr(business, 'vrn'):
            business.vrn = request.POST.get('vrn', '').strip()

        # Logo upload
        if 'logo' in request.FILES:
            logo = request.FILES['logo']
            # Simple validation
            if logo.size > 2 * 1024 * 1024:  # 2 MB
                messages.error(request, 'Logo must be under 2 MB')
            else:
                business.logo = logo

        # Remove logo
        if request.POST.get('remove_logo') == 'on' and business.logo:
            business.logo.delete(save=False)
            business.logo = None

        try:
            business.save()
            messages.success(request, 'Business settings updated successfully.')
            return redirect('business-settings')
        except Exception as e:
            messages.error(request, f'Error saving: {e}')

    return render(request, 'businesses/settings.html', {
        'business': business,
    })
