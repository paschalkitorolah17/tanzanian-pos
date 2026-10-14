from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal, InvalidOperation

from apps.accounts.decorators import role_required
from apps.products.models import Product, Category


@role_required('business_owner', 'manager', 'operator')
def product_list(request):
    business = request.user.business
    products = Product.objects.filter(
        business=business
    ).select_related('category').order_by('name')

    q = request.GET.get('q', '').strip()
    if q:
        products = products.filter(name__icontains=q) | products.filter(sku__icontains=q)

    return render(request, 'products/list.html', {
        'products': products,
        'q': q,
        'business': business,
    })


@role_required('business_owner', 'manager', 'operator')
def product_create(request):
    business = request.user.business
    categories = Category.objects.filter(business=business, is_active=True)

    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            sku = request.POST.get('sku', '').strip()
            barcode = request.POST.get('barcode', '').strip()
            category_id = request.POST.get('category') or None
            unit = request.POST.get('unit', 'pcs').strip()
            cost_price = Decimal(request.POST.get('cost_price') or '0')
            selling_price = Decimal(request.POST.get('selling_price') or '0')
            tax_status = request.POST.get('tax_status', 'taxable')
            tax_rate = Decimal(request.POST.get('tax_rate') or '18')
            reorder_level = Decimal(request.POST.get('reorder_level') or '0')
            description = request.POST.get('description', '').strip()

            if not name or not sku:
                raise ValueError('Name and SKU are required')
            if selling_price <= 0:
                raise ValueError('Selling price must be greater than zero')

            if Product.objects.filter(business=business, sku=sku).exists():
                raise ValueError(f'SKU "{sku}" already exists')

            product = Product(
                business=business,
                name=name,
                sku=sku,
                barcode=barcode,
                unit=unit,
                cost_price=cost_price,
                selling_price=selling_price,
                tax_status=tax_status,
                tax_rate=tax_rate,
                reorder_level=reorder_level,
                description=description,
            )
            if category_id:
                product.category = Category.objects.get(id=category_id, business=business)

            product.save()
            messages.success(request, f'Product "{name}" created successfully.')
            return redirect('product-list')

        except (ValueError, InvalidOperation) as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'products/form.html', {
        'categories': categories,
        'title': 'Add Product',
        'product': None,
    })


@role_required('business_owner', 'manager', 'operator')
def product_edit(request, pk):
    business = request.user.business
    product = get_object_or_404(Product, pk=pk, business=business)
    categories = Category.objects.filter(business=business, is_active=True)

    if request.method == 'POST':
        try:
            product.name = request.POST.get('name', '').strip()
            product.sku = request.POST.get('sku', '').strip()
            product.barcode = request.POST.get('barcode', '').strip()
            product.unit = request.POST.get('unit', 'pcs').strip()
            product.cost_price = Decimal(request.POST.get('cost_price') or '0')
            product.selling_price = Decimal(request.POST.get('selling_price') or '0')
            product.tax_status = request.POST.get('tax_status', 'taxable')
            product.tax_rate = Decimal(request.POST.get('tax_rate') or '18')
            product.reorder_level = Decimal(request.POST.get('reorder_level') or '0')
            product.description = request.POST.get('description', '').strip()
            product.is_active = request.POST.get('is_active') == 'on'

            category_id = request.POST.get('category') or None
            if category_id:
                product.category = Category.objects.get(id=category_id, business=business)
            else:
                product.category = None

            if not product.name or not product.sku:
                raise ValueError('Name and SKU are required')

            # Check SKU uniqueness excluding self
            if Product.objects.filter(business=business, sku=product.sku).exclude(pk=product.pk).exists():
                raise ValueError(f'SKU "{product.sku}" already exists')

            product.save()
            messages.success(request, f'Product "{product.name}" updated.')
            return redirect('product-list')

        except (ValueError, InvalidOperation) as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'products/form.html', {
        'categories': categories,
        'title': 'Edit Product',
        'product': product,
    })


@role_required('business_owner', 'manager', 'operator')
def category_list(request):
    business = request.user.business
    categories = Category.objects.filter(business=business).order_by('name')
    return render(request, 'products/category_list.html', {
        'categories': categories,
        'business': business,
    })


@role_required('business_owner', 'manager', 'operator')
def category_create(request):
    business = request.user.business

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Category name is required')
        elif Category.objects.filter(business=business, name=name).exists():
            messages.error(request, f'Category "{name}" already exists')
        else:
            Category.objects.create(
                business=business,
                name=name,
                description=description,
            )
            messages.success(request, f'Category "{name}" created.')
            return redirect('category-list')

    return render(request, 'products/category_form.html', {
        'title': 'Add Category',
        'category': None,
    })


@role_required('business_owner', 'manager', 'operator')
def category_edit(request, pk):
    business = request.user.business
    category = get_object_or_404(Category, pk=pk, business=business)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if not name:
            messages.error(request, 'Category name is required')
        elif Category.objects.filter(business=business, name=name).exclude(pk=pk).exists():
            messages.error(request, f'Category "{name}" already exists')
        else:
            category.name = name
            category.description = description
            category.is_active = is_active
            category.save()
            messages.success(request, f'Category "{name}" updated.')
            return redirect('category-list')

    return render(request, 'products/category_form.html', {
        'title': 'Edit Category',
        'category': category,
    })
