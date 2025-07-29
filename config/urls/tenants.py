from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.tenants.views import unified_login_view, tenant_dashboard_view, tenant_logout_view
from apps.core.views.health import health_check
from apps.core.views.debug import debug_main_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', unified_login_view, name='tenant_login'),
    path('login/', unified_login_view, name='unified_login'),
    path('health/', health_check, name='health_check'),  # Health check para tenants
    path('debug/', debug_main_view, name='debug_main'),  # Debug del template principal
    path('dashboard/', include('apps.dashboard.urls')),
    path('logout/', tenant_logout_view, name='tenant_logout'),
    path('accounting/', include('apps.accounting.urls')),
    path('expenses/', include('apps.expenses.urls')),
    path('invoicing/', include('apps.invoicing.urls')),
    path('core/', include('apps.core.urls')),  # Export functionality
]

# Configuración de archivos estáticos y media
# CRÍTICO: En producción con Whitenoise, no agregar static() URLs ya que Whitenoise las maneja
# Solo agregar en desarrollo local
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # En producción, solo servir archivos media (Whitenoise maneja static)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
