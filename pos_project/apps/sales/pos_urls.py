from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from apps.accounts.decorators import frontline_required
from .views import sale_receipt
from .pdf_views import sale_receipt_pdf

urlpatterns = [
    path(
        '',
        frontline_required(TemplateView.as_view(template_name='pos/pos.html')),
        name='pos'
    ),
    path('receipt/<int:sale_id>/', sale_receipt, name='sale-receipt'),
    path('receipt/<int:sale_id>/pdf/', sale_receipt_pdf, name='sale-receipt-pdf'),
]
