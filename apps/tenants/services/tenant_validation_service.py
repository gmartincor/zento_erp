from django.core.exceptions import ValidationError
from apps.tenants.models import Tenant

class TenantValidationService:
    @classmethod
    def validate_schema_name_format(cls, schema_name):
        temp_tenant = Tenant(schema_name=schema_name)
        try:
            temp_tenant._validate_schema_name()
            return True, None
        except ValidationError as e:
            error_msg = str(e)
            return False, error_msg
    
    @classmethod
    def check_schema_name_availability(cls, schema_name):
        return not Tenant.objects.filter(schema_name=schema_name).exists()
    
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
