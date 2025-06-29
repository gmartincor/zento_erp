from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.core.models import TimeStampedModel

User = get_user_model()


class RemanenteType(TimeStampedModel):
    name = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name="Nombre del tipo de remanente"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción del propósito de este tipo de remanente"
    )
    default_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Monto por defecto",
        help_text="Monto por defecto (puede ser positivo o negativo)"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        verbose_name="Creado por"
    )
    
    class Meta:
        db_table = 'remanente_types'
        verbose_name = "Tipo de Remanente"
        verbose_name_plural = "Tipos de Remanente"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        if self.default_amount is not None and self.default_amount == 0:
            raise ValidationError({
                'default_amount': 'El monto por defecto no puede ser cero. Use un valor positivo o negativo, o déjelo vacío.'
            })


class BusinessLineRemanenteConfig(TimeStampedModel):
    business_line = models.ForeignKey(
        'business_lines.BusinessLine', 
        on_delete=models.CASCADE, 
        related_name='remanente_configs',
        verbose_name="Línea de negocio"
    )
    remanente_type = models.ForeignKey(
        RemanenteType, 
        on_delete=models.CASCADE,
        verbose_name="Tipo de remanente"
    )
    is_enabled = models.BooleanField(
        default=True,
        verbose_name="Habilitado",
        help_text="Si este tipo de remanente está habilitado para esta línea de negocio"
    )
    default_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Monto por defecto específico",
        help_text="Monto por defecto específico para esta línea de negocio (sobrescribe el del tipo)"
    )
    
    class Meta:
        db_table = 'business_line_remanente_configs'
        unique_together = [['business_line', 'remanente_type']]
        verbose_name = "Configuración de Remanente por Línea"
        verbose_name_plural = "Configuraciones de Remanente por Línea"
        ordering = ['business_line__name', 'remanente_type__name']
    
    def __str__(self):
        return f"{self.business_line.name} - {self.remanente_type.name}"
    
    def get_effective_default_amount(self):
        return self.default_amount or self.remanente_type.default_amount
    
    def clean(self):
        if not self.business_line.allows_remanentes:
            raise ValidationError({
                'business_line': f'La línea de negocio "{self.business_line.name}" no tiene habilitados los remanentes.'
            })


class ServicePeriodRemanente(TimeStampedModel):
    client_service = models.ForeignKey(
        'accounting.ClientService', 
        on_delete=models.CASCADE, 
        related_name='period_remanentes',
        verbose_name="Servicio del cliente"
    )
    period_start = models.DateField(
        verbose_name="Inicio del período"
    )
    period_end = models.DateField(
        verbose_name="Fin del período"
    )
    remanente_type = models.ForeignKey(
        RemanenteType, 
        on_delete=models.CASCADE,
        verbose_name="Tipo de remanente"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Monto",
        help_text="Monto del remanente (puede ser positivo o negativo)"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notas",
        help_text="Notas adicionales sobre este remanente"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        verbose_name="Creado por"
    )
    
    class Meta:
        db_table = 'service_period_remanentes'
        unique_together = [['client_service', 'period_start', 'period_end', 'remanente_type']]
        verbose_name = "Remanente de Período"
        verbose_name_plural = "Remanentes de Período"
        ordering = ['-period_start', 'remanente_type__name']
    
    def __str__(self):
        return f"{self.client_service.client.full_name} - {self.remanente_type.name} ({self.period_start} a {self.period_end})"
    
    def clean(self):
        if not self.client_service.business_line.remanente_configs.filter(
            remanente_type=self.remanente_type,
            is_enabled=True
        ).exists():
            raise ValidationError({
                'remanente_type': f'La línea de negocio "{self.client_service.business_line.name}" '
                                f'no está configurada para usar remanentes de tipo "{self.remanente_type.name}"'
            })
        
        if self.period_start >= self.period_end:
            raise ValidationError({
                'period_end': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })
        
        if self.amount == 0:
            raise ValidationError({
                'amount': 'El monto del remanente no puede ser cero.'
            })
