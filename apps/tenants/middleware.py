from django.http import Http404
from django.db import connection
from django_tenants.middleware import TenantMainMiddleware
from django_tenants.utils import get_tenant_model, get_public_schema_name

class TenantSlugMiddleware(TenantMainMiddleware):
    """
    Middleware personalizado que extiende TenantMainMiddleware 
    para soportar identificación de tenant por slug en la URL
    en lugar de por dominio.
    """
    
    def process_request(self, request):
        # Obtener el schema público si la URL no tiene un slug de tenant
        connection.set_schema_to_public()
        
        # Verificar si hay un slug de tenant en la URL
        # Ejemplo: /tenant-slug/dashboard/
        path_parts = request.path_info.split('/')
        if len(path_parts) > 1 and path_parts[1]:
            tenant_slug = path_parts[1]
            
            # Verificar si estamos en una ruta que debe ser procesada por tenant
            if tenant_slug != 'admin' and tenant_slug != 'static' and tenant_slug != 'media':
                # Buscar tenant por slug
                TenantModel = get_tenant_model()
                try:
                    tenant = TenantModel.objects.get(
                        slug=tenant_slug,
                        is_active=True,
                        is_deleted=False
                    )
                    # Establecer el tenant en la conexión
                    connection.set_tenant(tenant)
                    request.tenant = tenant
                except TenantModel.DoesNotExist:
                    # Si no se encuentra el tenant, continuamos con el schema público
                    pass
            
        return None
