from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django_tenants.utils import connection
from apps.tenants.models import Tenant, Domain


class DevelopmentTenantMiddleware:
    """
    Middleware para manejar redirección automática de tenants en desarrollo.
    
    En desarrollo:
    - Si estás en localhost:8000 y autenticado, te redirige al subdominio correcto
    - Si intentas acceder a un subdominio que no funciona, usa un proxy interno
    
    En producción: 
    - No hace nada, django-tenants funciona normalmente
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo actuar en desarrollo
        if not settings.DEBUG:
            return self.get_response(request)
        
        # Verificar si necesitamos redirigir
        redirect_response = self._check_tenant_redirect(request)
        if redirect_response:
            return redirect_response
        
        response = self.get_response(request)
        return response
    
    def _check_tenant_redirect(self, request):
        """Verifica si necesitamos hacer una redirección de tenant"""
        current_host = request.get_host()
        current_tenant = connection.tenant
        
        # Si estamos en localhost:8000 (tenant público) y el usuario está autenticado
        if (current_host == 'localhost:8000' and 
            current_tenant.schema_name == 'public' and 
            request.user.is_authenticated and 
            hasattr(request.user, 'tenant') and 
            request.user.tenant and
            request.path == '/'):
            
            # Redirigir al subdominio del usuario
            user_tenant = request.user.tenant
            return self._redirect_to_tenant_subdomain(request, user_tenant)
        
        # Si estamos en un subdominio que no resuelve correctamente
        if (current_host != 'localhost:8000' and 
            current_host.endswith('.localhost:8000') and
            current_tenant.schema_name == 'public'):
            
            # Extraer el schema del subdominio
            subdomain = current_host.replace('.localhost:8000', '')
            target_tenant = Tenant.objects.filter(schema_name=subdomain).first()
            
            if target_tenant and request.user.is_authenticated:
                # Verificar que el usuario pertenece a este tenant
                if request.user.tenant == target_tenant:
                    # Redirigir al localhost con parámetro de tenant
                    tenant_param = f'?tenant={target_tenant.schema_name}'
                    path = request.path if request.path != '/' else ''
                    return HttpResponseRedirect(f'http://localhost:8000{path}{tenant_param}')
        
        return None
    
    def _redirect_to_tenant_subdomain(self, request, tenant):
        """Intenta redirigir al subdominio del tenant"""
        # Buscar dominio primario
        primary_domain = Domain.objects.filter(
            tenant=tenant, 
            is_primary=True
        ).first()
        
        if primary_domain:
            # Intentar redirección a subdominio
            subdomain_url = f'http://{primary_domain.domain}:8000{request.path}'
            
            # Primero, intentar con el subdominio
            # Si no funciona, el middleware lo detectará y volverá a localhost con parámetro
            return HttpResponseRedirect(subdomain_url)
        
        return None
