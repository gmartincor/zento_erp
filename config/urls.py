"""
URL configuration for the accounting project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_to_login(request):
    """Always redirect to login page as the entry point"""
    return redirect('authentication:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('auth/', include('apps.authentication.urls')),
    
    # App URLs
    path('dashboard/', include('apps.dashboard.urls')),
    path('accounting/', include('apps.accounting.urls')),
    path('expenses/', include('apps.expenses.urls')),
    
    # Root redirect - always go to login as entry point (must be last)
    path('', redirect_to_login),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
