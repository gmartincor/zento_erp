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
            
            # Manejar FakeTenant vs Tenant real
            if tenant:
                if hasattr(tenant, 'name'):
                    print(f"POST-TENANT DEBUG - Tenant name: {tenant.name}")
                else:
                    print(f"POST-TENANT DEBUG - Tenant type: {type(tenant).__name__} (no name attr)")
            else:
                print(f"POST-TENANT DEBUG - Tenant name: None")
        except Exception as e:
            print(f"POST-TENANT DEBUG ERROR: {e}")
        
        return response
