from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='core/landing.html'), name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('', include('apps.accounts.staff_urls')),
    path('api/v1/', include('apps.sales.api.urls')),
    path('api/v1/', include('apps.products.api.urls')),
    path('api/v1/', include('apps.payments.api.urls')),
    path('api/v1/', include('apps.customers.api_urls')),
    path('api/v1/', include('apps.payments.callback_urls')),
    path('pos/', include('apps.sales.pos_urls')),
    path('', include('apps.reports.urls')),
    path('', include('apps.expenses.urls')),
    path('', include('apps.purchases.urls')),
    path('', include('apps.products.urls')),
    path('', include('apps.customers.urls')),
    path('', include('apps.sales.history_urls')),
    path('', include('apps.inventory.urls')),
    path('', include('apps.suppliers.urls')),
    path('', include('apps.businesses.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
