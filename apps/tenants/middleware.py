from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import resolve, Resolver404
from django.utils.deprecation import MiddlewareMixin
from .models import Tenant


class TenantRouteMiddleware(MiddlewareMixin):
    def process_request(self, request):
        path = request.path_info
        
        if path.startswith('/admin/') or path.startswith('/static/') or path.startswith('/media/'):
            request.tenant = None
            return None
        
        if path == '/':
            request.tenant = None
            return None
        
        path_parts = [part for part in path.split('/') if part]
        
        if not path_parts:
            request.tenant = None
            return None
        
        potential_tenant_slug = path_parts[0]
        
        try:
            tenant = Tenant.objects.get(slug=potential_tenant_slug, is_active=True, is_deleted=False)
            request.tenant = tenant
            request.path_info = '/' + '/'.join(path_parts[1:]) + ('/' if path.endswith('/') and len(path_parts) > 1 else '')
            if not request.path_info.endswith('/') and request.path_info != '/':
                request.path_info += '/'
        except Tenant.DoesNotExist:
            request.tenant = None
        
        return None
