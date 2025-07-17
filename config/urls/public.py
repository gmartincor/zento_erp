from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from apps.tenants.views import unified_login_view, tenant_logout_view
from apps.core.views.health import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', unified_login_view, name='unified_login'),
    path('logout/', tenant_logout_view, name='tenant_logout'),
    path('health/', health_check, name='health_check'),
    path('guia/', TemplateView.as_view(template_name='core/system_guide.html'), name='system_guide'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
