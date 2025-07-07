from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context

from apps.core.constants import TENANT_SUCCESS_MESSAGES, TENANT_ERROR_MESSAGES
from apps.core.services import MessageService
from apps.tenants.models import Tenant, Domain

User = get_user_model()

class TenantService:
    @classmethod
    def create_tenant(cls, name, email, slug, **kwargs):
        try:
            with transaction.atomic():
                tenant = Tenant(
                    name=name,
                    email=email,
                    slug=slug,
                    schema_name=slug,
                    **kwargs
                )
                tenant.save()
                
                domain_str = f"{slug}.localhost"
                domain = Domain(
                    domain=domain_str,
                    tenant=tenant,
                    is_primary=True
                )
                domain.save()
                
                return tenant, domain
                
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(f"Error al crear tenant: {str(e)}")
    
    @classmethod
    def activate_tenant(cls, tenant_id, notes=None):
        try:
            tenant = Tenant.objects.get(pk=tenant_id)
            tenant.status = Tenant.StatusChoices.ACTIVE
            tenant.is_active = True
            
            if notes:
                tenant.notes = notes
                
            tenant.save(update_fields=['status', 'is_active', 'notes', 'updated'])
            return tenant
            
        except Tenant.DoesNotExist:
            raise ValidationError(TENANT_ERROR_MESSAGES['TENANT_NOT_FOUND'])
        except Exception as e:
            raise ValidationError(f"Error al activar tenant: {str(e)}")
    
    @classmethod
    def suspend_tenant(cls, tenant_id, reason=None):
        try:
            tenant = Tenant.objects.get(pk=tenant_id)
            tenant.status = Tenant.StatusChoices.SUSPENDED
            
            if reason:
                if tenant.notes:
                    tenant.notes += f"\n\nSuspendido: {reason}"
                else:
                    tenant.notes = f"Suspendido: {reason}"
                
            tenant.save(update_fields=['status', 'notes', 'updated'])
            return tenant
            
        except Tenant.DoesNotExist:
            raise ValidationError(TENANT_ERROR_MESSAGES['TENANT_NOT_FOUND'])
        except Exception as e:
            raise ValidationError(f"Error al suspender tenant: {str(e)}")
    
    @classmethod
    def execute_in_tenant_schema(cls, tenant, callable_function, *args, **kwargs):
        with schema_context(tenant.schema_name):
            return callable_function(*args, **kwargs)
