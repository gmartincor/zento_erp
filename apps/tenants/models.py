from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django_tenants.models import TenantMixin, DomainMixin
from apps.core.models import TimeStampedModel, SoftDeleteModel
from apps.core.constants import TENANT_ERROR_MESSAGES
from .managers import TenantManager, ActiveTenantManager, AllTenantManager


class Tenant(TenantMixin, TimeStampedModel, SoftDeleteModel):
    
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        ACTIVE = 'ACTIVE', 'Activo'
        SUSPENDED = 'SUSPENDED', 'Suspendido'
        INACTIVE = 'INACTIVE', 'Inactivo'
    
    name = models.CharField(
        max_length=255,
        verbose_name="Nombre del nutricionista",
        help_text="Nombre completo del profesional"
    )
    
    email = models.EmailField(
        unique=True,
        verbose_name="Correo electrónico",
        help_text="Email principal del nutricionista"
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono"
    )
    
    professional_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Número de colegiado",
        help_text="Número de colegiado profesional"
    )
    
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name="Estado",
        db_index=True
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Define si el tenant puede acceder al sistema"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Notas",
        help_text="Información adicional sobre el nutricionista"
    )
    
    objects = TenantManager()
    active_objects = ActiveTenantManager()
    all_objects = AllTenantManager()
    
    class Meta:
        db_table = 'tenants_tenant'
        verbose_name = "Nutricionista"
        verbose_name_plural = "Nutricionistas"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['is_deleted', 'status']),
        ]
    
    def clean(self):
        super().clean()
        if self.email:
            self._validate_unique_email()
    
    def _validate_unique_email(self):
        queryset = Tenant.objects.filter(
            email=self.email,
            is_deleted=False
        )
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        
        if queryset.exists():
            raise ValidationError({
                'email': TENANT_ERROR_MESSAGES['EMAIL_EXISTS'].format(email=self.email)
            })
    
    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower().strip()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.schema_name})"
    
    @property
    def is_available(self):
        return self.is_active and not self.is_deleted and self.status == self.StatusChoices.ACTIVE
    
    def activate(self):
        self.status = self.StatusChoices.ACTIVE
        self.is_active = True
        self.save(update_fields=['status', 'is_active', 'updated'])
    
    def suspend(self):
        self.status = self.StatusChoices.SUSPENDED
        self.save(update_fields=['status', 'updated'])
    
    def deactivate(self):
        self.status = self.StatusChoices.INACTIVE
        self.is_active = False
        self.save(update_fields=['status', 'is_active', 'updated'])


class Domain(DomainMixin):
    pass
