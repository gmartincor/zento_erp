"""
URL configuration for the accounting project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_to_login(request):
    return redirect('authentication:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Root redirect to login
    path('', redirect_to_login),
    
    # Authentication URLs
    path('auth/', include('apps.authentication.urls')),
    
    # App URLs
    path('dashboard/', include('apps.dashboard.urls')),
    path('accounting/', include('apps.accounting.urls')),
    path('expenses/', include('apps.expenses.urls')),
    path('business-lines/', include('apps.business_lines.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
