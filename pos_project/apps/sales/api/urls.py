from django.urls import path
from .views import CreateSaleAPIView

urlpatterns = [
    path('sales/', CreateSaleAPIView.as_view(), name='create-sale'),
]
