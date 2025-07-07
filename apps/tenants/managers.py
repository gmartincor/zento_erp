"""
Managers para el modelo Tenant aplicando principio DRY.
Reutiliza patrones de otros managers del sistema.
"""
from django.db import models
from django.core.exceptions import ValidationError
from apps.core.constants import TENANT_ERROR_MESSAGES


class TenantQuerySet(models.QuerySet):
    """QuerySet personalizado para Tenant aplicando principio DRY"""
    
    def active(self):
        """Obtener tenants activos y no eliminados"""
        return self.filter(
            is_active=True,
            is_deleted=False,
            status='ACTIVE'
        )
    
    def available(self):
        """Alias para active() - más semántico"""
        return self.active()
    
    def pending(self):
        """Obtener tenants pendientes de activación"""
        return self.filter(
            status='PENDING',
            is_deleted=False
        )
    
    def suspended(self):
        """Obtener tenants suspendidos"""
        return self.filter(
            status='SUSPENDED',
            is_deleted=False
        )
    
    def by_subdomain(self, subdomain):
        """Buscar por subdominio"""
        return self.filter(subdomain__iexact=subdomain)
    
    def by_email(self, email):
        """Buscar por email"""
        return self.filter(email__iexact=email)


class TenantManager(models.Manager):
    """Manager personalizado para Tenant aplicando principio DRY"""
    
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)
    
    def active(self):
        """Obtener tenants activos"""
        return self.get_queryset().active()
    
    def available(self):
        """Obtener tenants disponibles"""
        return self.get_queryset().available()
    
    def pending(self):
        """Obtener tenants pendientes"""
        return self.get_queryset().pending()
    
    def suspended(self):
        """Obtener tenants suspendidos"""
        return self.get_queryset().suspended()
    
    def get_by_subdomain(self, subdomain):
        """
        Obtener tenant por subdominio con validación.
        Reutiliza patrones de validación DRY.
        """
        try:
            return self.get_queryset().by_subdomain(subdomain).get()
        except self.model.DoesNotExist:
            raise ValidationError(TENANT_ERROR_MESSAGES['TENANT_NOT_FOUND'])
    
    def get_by_email(self, email):
        """
        Obtener tenant por email con validación.
        Reutiliza patrones de validación DRY.
        """
        try:
            return self.get_queryset().by_email(email).get()
        except self.model.DoesNotExist:
            raise ValidationError(TENANT_ERROR_MESSAGES['TENANT_NOT_FOUND'])
    
    def create_tenant(self, name, email, subdomain, **extra_fields):
        """
        Crear tenant con validaciones automáticas.
        Aplica principio DRY reutilizando validaciones del modelo.
        """
        # Validar duplicados antes de crear
        if self.get_queryset().by_subdomain(subdomain).exists():
            raise ValidationError(
                TENANT_ERROR_MESSAGES['SUBDOMAIN_EXISTS'].format(subdomain=subdomain)
            )
        
        if self.get_queryset().by_email(email).filter(is_deleted=False).exists():
            raise ValidationError(
                TENANT_ERROR_MESSAGES['EMAIL_EXISTS'].format(email=email)
            )
        
        # Crear tenant usando el método save que ya tiene todas las validaciones
        tenant = self.model(
            name=name,
            email=email,
            subdomain=subdomain,
            **extra_fields
        )
        
        # El método save() del modelo ya incluye full_clean()
        tenant.save()
        return tenant


class ActiveTenantManager(TenantManager):
    """Manager que solo retorna tenants activos por defecto"""
    
    def get_queryset(self):
        return super().get_queryset().active()


# Manager para incluir registros eliminados (soft delete)
class AllTenantManager(TenantManager):
    """Manager que incluye todos los tenants, incluso los eliminados"""
    
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)
