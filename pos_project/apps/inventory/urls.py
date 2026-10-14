from django.urls import path
from .views import stock_list, stock_movements

urlpatterns = [
    path('stock/', stock_list, name='stock-list'),
    path('stock/movements/', stock_movements, name='stock-movements'),
]
