from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django_tenants.utils import connection, get_tenant_model
from django.http import Http404

@login_required
def tenant_dashboard_view(request, tenant_slug=None):
    """Dashboard principal del tenant usando django-tenants con rutas basadas en slug"""
    # Obtener el tenant actual a través de la conexión (establecido por TenantMainMiddleware)
    tenant = connection.tenant
    
    # Verificar que el tenant está activo y que el slug coincide
    if not tenant or not tenant.is_active:
        messages.error(request, 'Acceso no disponible. Por favor, contacta al administrador.')
        return redirect('unified_login')
    
    # Verificar que el usuario tiene acceso a este tenant
    if tenant.slug != tenant_slug:
        raise Http404("Tenant no encontrado")
    
    context = {
        'tenant': tenant,
        'page_title': f'Dashboard - {tenant.name}',
        'show_tenant_branding': True,
    }
    
    return render(request, 'dashboard/home.html', context)


def tenant_logout_view(request):
    """Logout que siempre redirige al formulario unificado"""
    if request.user.is_authenticated:
        user_name = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f'¡Hasta pronto, {user_name}!')
    
    return redirect('unified_login')
