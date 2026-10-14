from django.urls import path
from .views import PosLoginView, PosLogoutView

app_name = 'accounts'

urlpatterns = [
    path('login/', PosLoginView.as_view(), name='login'),
    path('logout/', PosLogoutView.as_view(), name='logout'),
]
