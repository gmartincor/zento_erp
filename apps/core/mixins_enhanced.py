from django.core.exceptions import PermissionDenied
from django_tenants.utils import connection

class PageMetadataMixin:
    page_title = None
    subtitle = None
    
    def get_page_title(self):
        return self.page_title
        
    def get_subtitle(self):
        return self.subtitle
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': self.get_page_title(),
            'subtitle': self.get_subtitle(),
        })
        return context


class TenantUtilsMixin:
    def get_current_tenant(self):
        return connection.tenant
        
    def get_tenant_context(self):
        tenant = self.get_current_tenant()
        return {
            'tenant': tenant,
            'tenant_name': tenant.name if tenant else None,
            'tenant_schema': tenant.schema_name if tenant else None,
        }
        
    def validate_tenant_access(self, user, tenant=None):
        tenant = tenant or self.get_current_tenant()
        if not tenant or not tenant.is_active:
            raise PermissionDenied("Acceso no autorizado al tenant")
        return True


class QueryOptimizationMixin:
    select_related_fields = []
    prefetch_related_fields = []
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)
            
        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)
            
        return queryset
