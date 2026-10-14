"""
Generate printable barcode labels for products.
"""

from io import BytesIO
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from apps.accounts.decorators import role_required
from apps.products.models import Product


@role_required('business_owner', 'manager', 'operator')
def label_list(request):
    """Select products to print labels for."""
    business = request.user.business
    products = Product.objects.filter(
        business=business, is_active=True
    ).order_by('name')

    q = request.GET.get('q', '').strip()
    if q:
        products = products.filter(name__icontains=q) | products.filter(sku__icontains=q)

    return render(request, 'products/label_list.html', {
        'products': products[:100],
        'q': q,
        'business': business,
    })


@role_required('business_owner', 'manager', 'operator')
def print_labels(request):
    """
    Generate an HTML page of labels ready for printing.
    Expects POST with product_ids[] and optional quantity per product.
    """
    business = request.user.business
    product_ids = request.POST.getlist('product_ids')

    if not product_ids:
        from django.contrib import messages
        messages.error(request, 'Select at least one product')
        return redirect('label-list')

    labels = []
    for pid in product_ids:
        try:
            product = Product.objects.get(id=pid, business=business)
            qty = int(request.POST.get(f'qty_{pid}', 1))
            qty = max(1, min(qty, 50))  # safety limit
            for _ in range(qty):
                labels.append(product)
        except (Product.DoesNotExist, ValueError):
            continue

    return render(request, 'products/print_labels.html', {
        'labels': labels,
        'business': business,
    })


@login_required
def barcode_image(request, product_id):
    """Return a PNG barcode image for a product."""
    import barcode
    from barcode.writer import ImageWriter

    product = get_object_or_404(
        Product, id=product_id, business=request.user.business
    )

    # Prefer barcode field, fall back to SKU
    code = (product.barcode or product.sku or str(product.id)).strip()
    if not code:
        code = str(product.id)

    # Use Code128 (works with alphanumeric)
    CODE128 = barcode.get_barcode_class('code128')
    buffer = BytesIO()
    CODE128(code, writer=ImageWriter()).write(buffer, {
        'module_width': 0.3,
        'module_height': 12,
        'font_size': 8,
        'text_distance': 3,
        'quiet_zone': 2,
    })
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')
