from django.http import Http404
from django.db import connection
from django_tenants.middleware import TenantMainMiddleware
from django_tenants.utils import get_tenant_model, get_public_schema_name

class TenantSlugMiddleware(TenantMainMiddleware):

    

    IGNORED_PATHS = ['admin', 'static', 'media', 'favicon.ico']
    
    def process_request(self, request):

        # Iniciar con el esquema público por defecto
        connection.set_schema_to_public()
        
        # Extraer el posible slug del tenant de la URL
        path_parts = request.path_info.strip('/').split('/')
        if not path_parts:
            return None
            
        tenant_slug = path_parts[0]
        
        # Ignorar rutas administrativas y de recursos estáticos
        if tenant_slug in self.IGNORED_PATHS:
            return None
            
        # Intentar obtener el tenant por slug
        try:
            tenant = self.get_tenant_by_slug(tenant_slug)
            connection.set_tenant(tenant)
            request.tenant = tenant
        except:
            # Si no se encuentra el tenant, continuamos con el esquema público
            pass
            
        return None
        
    def get_tenant_by_slug(self, slug):
        """
        Obtiene un tenant activo por su slug.
        
        Args:
            slug: El slug del tenant a buscar
            
        Returns:
            El objeto tenant si se encuentra
            
        Raises:
            TenantModel.DoesNotExist: Si no se encuentra un tenant con ese slug
        """
        TenantModel = get_tenant_model()
        return TenantModel.objects.get(
            slug=slug,
            is_active=True,
            is_deleted=False
        )
