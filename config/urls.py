from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from apps.tenants.tenant_views import tenant_login_view, tenant_dashboard_view, tenant_logout_view

def redirect_to_admin(request):
    return redirect('admin:index')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('<str:tenant_slug>/', include([
        path('', tenant_dashboard_view, name='tenant_dashboard'),
        path('login/', tenant_login_view, name='tenant_login'),
        path('logout/', tenant_logout_view, name='tenant_logout'),
        path('logout/', tenant_logout_view, name='tenant_logout'),
        path('auth/', include('apps.authentication.urls')),
        path('dashboard/', include('apps.dashboard.urls')),
        path('accounting/', include('apps.accounting.urls')),
        path('expenses/', include('apps.expenses.urls')),
    ])),
    
    path('', redirect_to_admin),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
