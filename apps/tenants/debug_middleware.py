import logging

logger = logging.getLogger(__name__)

class TenantDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f"PRE-TENANT DEBUG - Host: {request.get_host()}")
        print(f"PRE-TENANT DEBUG - Path: {request.path}")
        print(f"PRE-TENANT DEBUG - META HOST: {request.META.get('HTTP_HOST', 'None')}")
        print(f"PRE-TENANT DEBUG - SERVER NAME: {request.META.get('SERVER_NAME', 'None')}")
        print(f"PRE-TENANT DEBUG - SERVER PORT: {request.META.get('SERVER_PORT', 'None')}")
        
        response = self.get_response(request)
        
        try:
            from django_tenants.utils import connection
            tenant = connection.tenant
            print(f"POST-TENANT DEBUG - Tenant: {tenant.schema_name if tenant else 'None'}")
            print(f"POST-TENANT DEBUG - Tenant name: {tenant.name if tenant else 'None'}")
        except Exception as e:
            print(f"POST-TENANT DEBUG ERROR: {e}")
        
        return response
