from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.tenants.views import tenant_dashboard_view, tenant_logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', tenant_dashboard_view, name='tenant_dashboard'),
    path('dashboard/', tenant_dashboard_view, name='dashboard_home'),
    path('logout/', tenant_logout_view, name='tenant_logout'),
    
    path('accounting/', include('apps.accounting.urls')),
    path('expenses/', include('apps.expenses.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
