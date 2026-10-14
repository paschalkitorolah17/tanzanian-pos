from django.urls import path
from .views import switch_branch
from .settings_views import business_settings

urlpatterns = [
    path('switch-branch/', switch_branch, name='switch-branch'),
    path('settings/', business_settings, name='business-settings'),
]
