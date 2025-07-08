import logging
from django.http import HttpResponse
from django_tenants.utils import connection

logger = logging.getLogger(__name__)

class TenantDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f"DEBUG: Host header: {request.get_host()}")
        print(f"DEBUG: HTTP_HOST: {request.META.get('HTTP_HOST')}")
        
        try:
            tenant = connection.tenant
            print(f"DEBUG: Current tenant: {tenant}")
            print(f"DEBUG: Tenant schema: {tenant.schema_name}")
        except Exception as e:
            print(f"DEBUG: Error getting tenant: {e}")
            
        response = self.get_response(request)
        return response
