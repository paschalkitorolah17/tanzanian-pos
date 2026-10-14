from django.urls import path
from .api_views import QuickCustomerCreateAPIView

urlpatterns = [
    path('customers/quick/', QuickCustomerCreateAPIView.as_view(), name='quick-customer'),
]
