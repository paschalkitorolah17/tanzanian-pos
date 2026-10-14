from django.urls import path
from .history_views import sales_history, sale_detail
from .return_views import process_return

urlpatterns = [
    path('sales/', sales_history, name='sales-history'),
    path('sales/<int:pk>/', sale_detail, name='sale-detail'),
    path('sales/<int:sale_id>/return/', process_return, name='process-return'),
]
