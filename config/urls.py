from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from apps.tenants.tenant_views import tenant_dashboard_view, tenant_logout_view
from apps.tenants.unified_views import unified_login_view

def redirect_to_admin(request):
    return redirect('admin:index')

def redirect_to_unified_login(request, tenant_slug=None):
    return redirect('unified_login')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('<str:tenant_slug>/', tenant_dashboard_view, name='tenant_dashboard'),
    path('<str:tenant_slug>/login/', redirect_to_unified_login, name='tenant_login'),
    path('<str:tenant_slug>/logout/', tenant_logout_view, name='tenant_logout'),
    path('<str:tenant_slug>/dashboard/', tenant_dashboard_view, name='dashboard_home'),
    path('<str:tenant_slug>/accounting/', include('apps.accounting.urls')),
    path('<str:tenant_slug>/expenses/', include('apps.expenses.urls')),
    
    path('', unified_login_view, name='unified_login'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
