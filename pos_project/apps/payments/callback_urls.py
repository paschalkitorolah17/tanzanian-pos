from django.urls import path
from .callback_views import mpesa_callback

urlpatterns = [
    path('payments/mpesa/callback/', mpesa_callback, name='mpesa-callback'),
]
