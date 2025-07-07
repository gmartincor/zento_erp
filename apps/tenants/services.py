from django.db import transaction
from django.core.exceptions import ValidationError
from apps.core.constants import TENANT_ERROR_MESSAGES, TENANT_SUCCESS_MESSAGES, TENANT_DEFAULTS
from .models import Tenant


class TenantService:
    @staticmethod
    def create_tenant(name, email, subdomain, **extra_fields):
        try:
            with transaction.atomic():
                tenant = Tenant.objects.create_tenant(
                    name=name,
                    email=email,
                    subdomain=subdomain,
                    **extra_fields
                )
                return tenant
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Error creando tenant: {str(e)}")
    
    @staticmethod
    def activate_tenant(tenant_id):
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            tenant.activate()
            return tenant
        except Tenant.DoesNotExist:
            raise ValidationError(TENANT_ERROR_MESSAGES['TENANT_NOT_FOUND'])
    
    @staticmethod
    def deactivate_tenant(tenant_id):
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            tenant.soft_delete()
            return tenant
        except Tenant.DoesNotExist:
            raise ValidationError(TENANT_ERROR_MESSAGES['TENANT_NOT_FOUND'])
    
    @staticmethod
    def suspend_tenant(tenant_id, reason=None):
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            tenant.suspend(reason=reason)
            return tenant
        except Tenant.DoesNotExist:
            raise ValidationError(TENANT_ERROR_MESSAGES['TENANT_NOT_FOUND'])
    
    @staticmethod
    def get_tenant_by_subdomain(subdomain):
        try:
            return Tenant.objects.get_by_subdomain(subdomain)
        except ValidationError:
            return None
    
    @staticmethod
    def get_tenant_by_email(email):
        try:
            return Tenant.objects.get_by_email(email)
        except ValidationError:
            return None
    
    @staticmethod
    def get_active_tenants():
        return Tenant.active_objects.all()
    
    @staticmethod
    def get_pending_tenants():
        return Tenant.objects.pending()
    
    @staticmethod
    def validate_tenant_access(tenant):
        if not tenant:
            raise ValidationError(TENANT_ERROR_MESSAGES['TENANT_NOT_FOUND'])
        if not tenant.is_available:
            if tenant.status == Tenant.StatusChoices.SUSPENDED:
                raise ValidationError(TENANT_ERROR_MESSAGES['TENANT_SUSPENDED'])
            else:
                raise ValidationError(TENANT_ERROR_MESSAGES['TENANT_INACTIVE'])
        return True


class TenantDataService:
    @staticmethod
    def execute_in_tenant_context(tenant, operation, *args, **kwargs):
        if not tenant.is_available:
            raise ValidationError(TENANT_ERROR_MESSAGES['TENANT_INACTIVE'])
        return operation(*args, **kwargs)
    
    @staticmethod
    def create_sample_data_for_tenant(tenant):
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
        return TenantDataService.execute_in_tenant_context(
            tenant, _create_sample_data
        )
    
    @staticmethod
    def migrate_tenant_schema(tenant):
        return True


class TenantValidationService:
    @staticmethod
    def validate_subdomain_format(subdomain):
        temp_tenant = Tenant(subdomain=subdomain)
        try:
            temp_tenant._validate_subdomain()
            return True, None
        except ValidationError as e:
            error_msg = e.message_dict.get('subdomain', ['Error de validación'])[0]
            return False, error_msg
    
    @staticmethod
    def check_subdomain_availability(subdomain):
        return not Tenant.objects.by_subdomain(subdomain).exists()
    
    @staticmethod
    def check_email_availability(email):
        return not Tenant.objects.by_email(email).filter(is_deleted=False).exists()
