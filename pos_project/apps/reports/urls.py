from django.urls import path
from .views import (
    dashboard, sales_report, sales_report_csv,
    profit_loss_report, expense_report,
)

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('reports/sales/', sales_report, name='sales-report'),
    path('reports/sales/csv/', sales_report_csv, name='sales-report-csv'),
    path('reports/profit-loss/', profit_loss_report, name='profit-loss'),
    path('reports/expenses/', expense_report, name='expense-report'),
]
