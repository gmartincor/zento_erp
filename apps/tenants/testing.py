from django_tenants.utils import tenant_context
from apps.tenants.models import Tenant
from apps.accounting.models import Client as AccountingClient


class TenantTestingService:
    @staticmethod
    def verify_isolation():
        results = []
        tenants = Tenant.objects.all()
        
        for tenant in tenants:
            with tenant_context(tenant):
                client_count = AccountingClient.objects.count()
                results.append({
                    'tenant_name': tenant.name,
                    'schema': tenant.schema_name,
                    'subdomain': tenant.subdomain,
                    'client_count': client_count,
                    'is_isolated': True
                })
        
        return results
    
    @staticmethod
    def create_test_data(tenant, test_data):
        with tenant_context(tenant):
            created_objects = []
            
            for client_data in test_data.get('clients', []):
                client = AccountingClient.objects.create(**client_data)
                created_objects.append({
                    'type': 'client',
                    'id': client.id,
                    'name': client.full_name
                })
            
            return created_objects
    
    @staticmethod
    def cleanup_test_data(tenant):
        with tenant_context(tenant):
            deleted_count = AccountingClient.objects.filter(
                dni__startswith='TEST'
            ).delete()[0]
            return deleted_count
