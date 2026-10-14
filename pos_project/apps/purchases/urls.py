from django.urls import path
from .views import purchase_list, receive_stock

urlpatterns = [
    path('purchases/', purchase_list, name='purchase-list'),
    path('purchases/receive/', receive_stock, name='receive-stock'),
]
