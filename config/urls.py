from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from apps.tenants.views import unified_login_view

def redirect_to_admin(request):
    return redirect('admin:index')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', unified_login_view, name='unified_login'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
