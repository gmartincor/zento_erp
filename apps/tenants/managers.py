from django.db import models
from django.core.exceptions import ValidationError
from apps.core.constants import TENANT_ERROR_MESSAGES


class TenantQuerySet(models.QuerySet):
    
    def active(self):
        return self.filter(
            is_active=True,
            is_deleted=False,
            status='ACTIVE'
        )
    
    def available(self):
        return self.active()
    
    def pending(self):
        return self.filter(
            status='PENDING',
            is_deleted=False
        )
    
    def suspended(self):
        return self.filter(
            status='SUSPENDED',
            is_deleted=False
        )
    
    def by_email(self, email):
        return self.filter(email__iexact=email)


class TenantManager(models.Manager):
    
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def available(self):
        return self.get_queryset().available()
    
    def pending(self):
        return self.get_queryset().pending()
    
    def suspended(self):
        return self.get_queryset().suspended()
    
    def get_by_email(self, email):
        try:
            return self.get_queryset().by_email(email).get()
        except self.model.DoesNotExist:
            raise ValidationError(TENANT_ERROR_MESSAGES['TENANT_NOT_FOUND'])
    
    def create_tenant(self, name, email, schema_name, **extra_fields):
        if self.get_queryset().by_email(email).filter(is_deleted=False).exists():
            raise ValidationError(
                TENANT_ERROR_MESSAGES['EMAIL_EXISTS'].format(email=email)
            )
        
        tenant = self.model(
            name=name,
            email=email,
            schema_name=schema_name,
            **extra_fields
        )
        
        tenant.save()
        return tenant


class ActiveTenantManager(TenantManager):
    
    def get_queryset(self):
        return super().get_queryset().active()


class AllTenantManager(TenantManager):
    
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)
