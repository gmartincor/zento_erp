from django.conf import settings
from django_tenants.utils import connection


def tenant_context(request):
    """
    Context processor que proporciona información del tenant
    y URLs correctas para desarrollo y producción
    """
    current_tenant = connection.tenant
    context = {}
    
    # Información básica del tenant
    context['current_tenant'] = current_tenant
    context['is_public_tenant'] = current_tenant.schema_name == 'public'
    
    # En desarrollo, proporcionar URLs que funcionen con el sistema de parámetros
    if settings.DEBUG and hasattr(request, 'user') and request.user.is_authenticated:
        tenant_param = ''
        
        # Si estamos en modo desarrollo con parámetro de tenant
        if request.GET.get('tenant'):
            tenant_param = f'?tenant={request.GET.get("tenant")}'
        elif hasattr(request.user, 'tenant') and request.user.tenant:
            tenant_param = f'?tenant={request.user.tenant.schema_name}'
        
        context['dev_urls'] = {
            'dashboard': f'/{tenant_param}',
            'accounting': f'/accounting/{tenant_param}',
            'expenses': f'/expenses/{tenant_param}',
            'logout': f'/logout/{tenant_param}',
        }
    
    return context
