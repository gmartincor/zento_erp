from django.core.exceptions import ValidationError
from apps.tenants.models import Tenant

class TenantValidationService:
    @classmethod
    def validate_subdomain_format(cls, subdomain):
        temp_tenant = Tenant(slug=subdomain, schema_name=subdomain)
        try:
            temp_tenant._validate_schema_name()
            return True, None
        except ValidationError as e:
            error_msg = e.message_dict.get('slug', ['Error de validación'])[0]
            return False, error_msg
    
    @classmethod
    def check_subdomain_availability(cls, subdomain):
        return not Tenant.objects.filter(schema_name=subdomain).exists()
    
    @classmethod
    def check_email_availability(cls, email):
        return not Tenant.objects.filter(email=email, is_deleted=False).exists()
    
    @classmethod
    def validate_tenant_access(cls, tenant):
        if not tenant:
            raise ValidationError("Tenant no encontrado")
        if not tenant.is_available:
            if tenant.status == Tenant.StatusChoices.SUSPENDED:
                raise ValidationError("El tenant está suspendido")
            else:
                raise ValidationError("El tenant no está activo")
        return True
