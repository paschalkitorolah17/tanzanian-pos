from django.urls import path
from .staff_views import staff_list, staff_create

urlpatterns = [
    path('staff/', staff_list, name='staff-list'),
    path('staff/add/', staff_create, name='staff-create'),
]
