from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from apps.sales.models import Sale
from apps.sales.pdf_receipt import generate_receipt_pdf


@login_required
def sale_receipt_pdf(request, sale_id):
    sale = get_object_or_404(
        Sale.objects.select_related(
            'business', 'branch', 'cashier', 'customer'
        ).prefetch_related(
            'items__product', 'payments__payment_method'
        ),
        id=sale_id,
        business=request.user.business
    )

    pdf_buffer = generate_receipt_pdf(sale)

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="receipt_{sale.transaction_number}.pdf"'
    )
    return response
