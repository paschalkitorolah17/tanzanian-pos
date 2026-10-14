from django.urls import path
from .views import expense_list, expense_create, expense_csv

urlpatterns = [
    path('expenses/', expense_list, name='expense-list'),
    path('expenses/add/', expense_create, name='expense-create'),
    path('expenses/csv/', expense_csv, name='expense-csv'),
]
