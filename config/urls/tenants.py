from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.tenants.views import unified_login_view, tenant_dashboard_view, tenant_logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', unified_login_view, name='tenant_login'),
    path('login/', unified_login_view, name='unified_login'),
    path('dashboard/', tenant_dashboard_view, name='tenant_dashboard'),
    path('logout/', tenant_logout_view, name='tenant_logout'),
    path('accounting/', include('apps.accounting.urls')),
    path('expenses/', include('apps.expenses.urls')),
    path('invoicing/', include('apps.invoicing.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
