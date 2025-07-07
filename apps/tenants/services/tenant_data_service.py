from django.core.exceptions import ValidationError
from django_tenants.utils import schema_context

from apps.core.constants import TENANT_ERROR_MESSAGES
from apps.tenants.models import Tenant

class TenantDataService:
    @classmethod
    def execute_in_tenant_context(cls, tenant, operation, *args, **kwargs):
        if not tenant.is_available:
            raise ValidationError(TENANT_ERROR_MESSAGES['TENANT_INACTIVE'])
            
        with schema_context(tenant.schema_name):
            return operation(*args, **kwargs)
    
    @classmethod
    def create_sample_data_for_tenant(cls, tenant):
        tenant.refresh_from_db()
        
        def _create_sample_data():
            from apps.business_lines.models import BusinessLine
            if not BusinessLine.objects.exists():
                main_lines = [
                    "Consultoría Nutricional",
                    "Planes Alimentarios",
                    "Seguimiento Nutricional"
                ]
                for line_name in main_lines:
                    BusinessLine.objects.create(
                        name=line_name,
                        is_active=True
                    )
            return True
            
        return cls.execute_in_tenant_context(
            tenant, _create_sample_data
        )
    
    @classmethod
    def migrate_tenant_schema(cls, tenant):
        return True
