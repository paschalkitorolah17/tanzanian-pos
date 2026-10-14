from django.urls import path
from .views import customer_list, customer_create, customer_edit

urlpatterns = [
    path('customers/', customer_list, name='customer-list'),
    path('customers/add/', customer_create, name='customer-create'),
    path('customers/<int:pk>/edit/', customer_edit, name='customer-edit'),
]
