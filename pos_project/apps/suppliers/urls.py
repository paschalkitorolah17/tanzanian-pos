from django.urls import path
from .views import supplier_list, supplier_create, supplier_edit

urlpatterns = [
    path('suppliers/', supplier_list, name='supplier-list'),
    path('suppliers/add/', supplier_create, name='supplier-create'),
    path('suppliers/<int:pk>/edit/', supplier_edit, name='supplier-edit'),
]
