from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import TimeStampedModel, SoftDeleteModel
from apps.business_lines.models import BusinessLine
from .managers.client_service_manager import ClientServiceManager


class Client(TimeStampedModel, SoftDeleteModel):
    
    class GenderChoices(models.TextChoices):
        MALE = 'M', 'Masculino'
        FEMALE = 'F', 'Femenino'
        OTHER = 'O', 'Otro'
    
    full_name = models.CharField(
        max_length=255,
        verbose_name="Nombre completo"
    )
    
    dni = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="DNI/NIE",
        help_text="Documento de identidad único"
    )
    
    gender = models.CharField(
        max_length=1,
        choices=GenderChoices.choices,
        verbose_name="Género"
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name="Correo electrónico"
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Teléfono"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Notas",
        help_text="Información adicional sobre el cliente"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        db_index=True
    )

    class Meta:
        db_table = 'clients'
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        indexes = [
            models.Index(fields=['dni']),
            models.Index(fields=['is_active', 'full_name']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.dni})"
    
    def save(self, *args, **kwargs):
        is_update = self.pk is not None
        original_is_active = None
        
        if is_update:
            original_instance = Client.objects.get(pk=self.pk)
            original_is_active = original_instance.is_active
        
        super().save(*args, **kwargs)
        
        if is_update and original_is_active is not None and original_is_active != self.is_active:
            self._handle_activation_change()
    
    def _handle_activation_change(self):
        from .services.client_state_manager import ClientStateManager
        
        if self.is_active:
            ClientStateManager.reactivate_client(self)
        else:
            ClientStateManager.deactivate_client(self)


class ClientService(TimeStampedModel):
    
    class CategoryChoices(models.TextChoices):
        WHITE = 'white', 'Blanco'
        BLACK = 'black', 'Negro'
    
    class AdminStatusChoices(models.TextChoices):
        ENABLED = 'ENABLED', 'Habilitado'
        SUSPENDED = 'SUSPENDED', 'Suspendido temporalmente'
        DISABLED = 'DISABLED', 'Deshabilitado administrativamente'
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name="Cliente"
    )
    
    business_line = models.ForeignKey(
        'business_lines.BusinessLine',
        on_delete=models.CASCADE,
        related_name='client_services',
        verbose_name="Línea de negocio"
    )
    
    category = models.CharField(
        max_length=10,
        choices=CategoryChoices.choices,
        verbose_name="Categoría"
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Precio base"
    )
    
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de inicio"
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de finalización"
    )
    
    admin_status = models.CharField(
        max_length=15,
        choices=AdminStatusChoices.choices,
        default=AdminStatusChoices.ENABLED,
        verbose_name="Estado administrativo",
        help_text="Control administrativo independiente del estado operacional"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Notas del servicio",
        help_text="Observaciones específicas del servicio"
    )
    
    remanentes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Remanentes",
        help_text="Información de remanentes para categoría BLACK"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        db_index=True
    )

    objects = ClientServiceManager()

    class Meta:
        db_table = 'client_services'
        verbose_name = "Servicio de cliente"
        verbose_name_plural = "Servicios de clientes"
        indexes = [
            models.Index(fields=['client', 'is_active']),
            models.Index(fields=['business_line', 'category']),
            models.Index(fields=['client', 'business_line', 'category', 'created']),
        ]

    def clean(self):
        super().clean()
        
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({
                'end_date': 'La fecha de finalización debe ser posterior a la fecha de inicio.'
            })
        
        if self.price < 0:
            raise ValidationError({
                'price': 'El precio no puede ser negativo.'
            })
        
        if self.category != self.CategoryChoices.BLACK and self.remanentes:
            raise ValidationError({
                'remanentes': 'Los remanentes solo pueden configurarse para la categoría BLACK.'
            })
        
        if self.category == self.CategoryChoices.BLACK and not isinstance(self.remanentes, dict):
            raise ValidationError({
                'remanentes': 'Los remanentes deben ser un diccionario válido para la categoría BLACK.'
            })
        
        if self.category == self.CategoryChoices.BLACK:
            if not self.business_line_id:
                return
            
            if not self.business_line.has_remanente or not self.business_line.remanente_field:
                raise ValidationError({
                    'business_line': f'La línea de negocio "{self.business_line.name}" no tiene un tipo de remanente configurado.'
                })
            
            business_line_name = self.business_line.name.lower()
            expected_remanente = None
            
            if "pepe-normal" in business_line_name:
                expected_remanente = BusinessLine.RemanenteChoices.REMANENTE_PEPE
            elif "pepe-videocall" in business_line_name:
                expected_remanente = BusinessLine.RemanenteChoices.REMANENTE_PEPE_VIDEO
            elif "dani-rubi" in business_line_name:
                expected_remanente = BusinessLine.RemanenteChoices.REMANENTE_DANI
            elif "dani" in business_line_name and "rubi" not in business_line_name:
                expected_remanente = BusinessLine.RemanenteChoices.REMANENTE_AVEN
                
            if expected_remanente and self.business_line.remanente_field != expected_remanente:
                raise ValidationError({
                    'business_line': f'La línea de negocio "{self.business_line.name}" debe usar el tipo de remanente "{expected_remanente}".'
                })
            
            if self.remanentes and isinstance(self.remanentes, dict):
                valid_keys = {self.business_line.remanente_field}
                invalid_keys = set(self.remanentes.keys()) - valid_keys
                
                if invalid_keys:
                    raise ValidationError({
                        'remanentes': f'El campo de remanentes contiene claves no válidas para esta línea de negocio: {", ".join(invalid_keys)}. '
                                     f'Solo se permite la clave "{self.business_line.remanente_field}" para la línea "{self.business_line.name}".'
                    })

    def save(self, *args, **kwargs):
        if self.category != self.CategoryChoices.BLACK:
            self.remanentes = {}
        
        elif self.category == self.CategoryChoices.BLACK and not isinstance(self.remanentes, dict):
            self.remanentes = {}
        
        elif self.category == self.CategoryChoices.BLACK and self.business_line_id and self.business_line.remanente_field:
            valid_key = self.business_line.remanente_field
            if valid_key in self.remanentes:
                valid_value = self.remanentes[valid_key]
                self.remanentes = {valid_key: valid_value}
            else:
                self.remanentes = {}
        
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client.full_name} - {self.business_line.name} ({self.category})"

    def get_remanente_total(self):
        if self.category == self.CategoryChoices.BLACK and self.remanentes:
            total = 0
            for value in self.remanentes.values():
                try:
                    total += float(value)
                except (ValueError, TypeError):
                    pass
            return total
        return 0
    
    @property
    def is_expired(self):
        from .services.service_state_manager import ServiceStateManager
        return ServiceStateManager.is_service_expired(self)
    
    @property
    def days_until_expiry(self):
        from .services.service_state_manager import ServiceStateManager
        return ServiceStateManager.days_until_expiry(self)
    
    @property
    def needs_renewal(self):
        from .services.service_state_manager import ServiceStateManager
        return ServiceStateManager.needs_renewal(self)

    @property
    def current_status(self):
        from .services.service_state_manager import ServiceStateManager
        return ServiceStateManager.get_service_status(self)

    @property
    def status_display_data(self):
        from .services.service_state_manager import ServiceStateManager
        return ServiceStateManager.get_status_display_data(self)

    def get_status_display(self):
        from .services.service_state_manager import ServiceStateManager
        return ServiceStateManager.get_status_display(self.current_status)

    def get_payment_timing_analysis(self):
        from .services.payment_service import PaymentService
        return PaymentService.analyze_payment_timing(self)

    @property
    def total_paid(self):
        from .services.payment_service import PaymentService
        self.invalidate_payment_cache()
        return PaymentService.get_service_total_paid(self)

    @property
    def payment_count(self):
        from .services.payment_service import PaymentService
        return PaymentService.get_service_payment_count(self)

    @property
    def current_amount(self):
        from .services.payment_service import PaymentService
        return PaymentService.get_service_current_amount(self)

    @property
    def current_payment_method(self):
        from .services.payment_service import PaymentService
        return PaymentService.get_service_current_payment_method(self)

    def get_payment_method_display(self):
        method = self.current_payment_method
        if not method:
            return "No definido"
        
        payment_choices = dict(ServicePayment.PaymentMethodChoices.choices)
        return payment_choices.get(method, method)

    def get_line_path(self):
        """
        Obtiene el path jerárquico de la línea de negocio para usar en URLs.
        Nunca retorna una cadena vacía.
        """
        if self.business_line:
            path = self.business_line.get_url_path()
            return path if path else 'default'
        return 'default'

    def invalidate_payment_cache(self):
        if hasattr(self, '_prefetched_objects_cache'):
            self._prefetched_objects_cache.pop('payments', None)

    def get_fresh_service_data(self):
        self.invalidate_payment_cache()
        self.refresh_from_db()
        return self

    def can_edit_dates(self):
        from .services.service_manager import ServiceManager
        return ServiceManager.can_edit_service_dates(self)
    
    def get_date_edit_info(self):
        from .services.service_manager import ServiceManager
        return ServiceManager.get_date_edit_restrictions(self)


class ServicePayment(TimeStampedModel):
    
    class StatusChoices(models.TextChoices):
        PERIOD_CREATED = 'PERIOD_CREATED', 'Período creado (sin pago)'
        PENDING = 'PENDING', 'Pendiente'
        PAID = 'PAID', 'Pagado'
        OVERDUE = 'OVERDUE', 'Vencido'
        CANCELLED = 'CANCELLED', 'Cancelado'
        REFUNDED = 'REFUNDED', 'Reembolsado'
    
    class PaymentMethodChoices(models.TextChoices):
        CARD = 'CARD', 'Tarjeta'
        CASH = 'CASH', 'Efectivo'
        TRANSFER = 'TRANSFER', 'Transferencia'
        BIZUM = 'BIZUM', 'Bizum'
        PAYPAL = 'PAYPAL', 'PayPal'
        OTHER = 'OTHER', 'Otro'
    
    client_service = models.ForeignKey(
        ClientService,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="Servicio"
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto",
        help_text="Monto del pago (opcional para períodos sin pago)"
    )
    
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de pago",
        help_text="Fecha de pago (opcional para períodos sin pago)"
    )
    
    period_start = models.DateField(
        verbose_name="Inicio del período"
    )
    
    period_end = models.DateField(
        verbose_name="Fin del período"
    )
    
    status = models.CharField(
        max_length=15,
        choices=StatusChoices.choices,
        default=StatusChoices.PERIOD_CREATED,
        verbose_name="Estado"
    )
    
    payment_method = models.CharField(
        max_length=15,
        choices=PaymentMethodChoices.choices,
        null=True,
        blank=True,
        verbose_name="Método de pago",
        help_text="Método de pago (opcional para períodos sin pago)"
    )
    
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Número de referencia",
        help_text="Referencia de la transacción"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Notas"
    )

    class Meta:
        db_table = 'service_payments'
        verbose_name = "Pago de servicio"
        verbose_name_plural = "Pagos de servicios"
        indexes = [
            models.Index(fields=['client_service', 'status']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['status', 'payment_date']),
        ]
        ordering = ['-payment_date', '-created']

    def clean(self):
        super().clean()
        
        if self.period_start and self.period_end and self.period_start >= self.period_end:
            raise ValidationError({
                'period_end': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })
        
        if self.payment_date and self.period_start and self.payment_date > self.period_end:
            raise ValidationError({
                'payment_date': 'La fecha de pago no puede ser posterior al fin del período.'
            })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client_service.client.full_name} - {self.amount}€ ({self.get_status_display()})"

    @property
    def duration_days(self):
        if self.period_start and self.period_end:
            return (self.period_end - self.period_start).days + 1
        return 0

    @property
    def is_active_period(self):
        if not self.period_start or not self.period_end:
            return False
        today = timezone.now().date()
        return self.period_start <= today <= self.period_end

    @property
    def days_until_expiry(self):
        if not self.period_end:
            return None
        today = timezone.now().date()
        return (self.period_end - today).days

    @property
    def days_until_due(self):
        if self.status == self.StatusChoices.PAID:
            return None
        today = timezone.now().date()
        return (self.period_end - today).days

    @property
    def is_payment_overdue(self):
        if self.status == self.StatusChoices.PAID:
            return False
        return timezone.now().date() > self.period_end

    @property
    def was_paid_on_time(self):
        if self.status != self.StatusChoices.PAID:
            return None
        return self.payment_date <= self.period_end

    @property
    def days_paid_late(self):
        if not self.was_paid_on_time:
            return 0
        return (self.payment_date - self.period_end).days

    @property
    def payment_status_detailed(self):
        if self.status == self.StatusChoices.PAID:
            return "PAID_ON_TIME" if self.was_paid_on_time else "PAID_LATE"
        
        days_left = self.days_until_due
        if days_left is None:
            return "UNKNOWN"
        elif days_left > 7:
            return "PENDING_OK"
        elif days_left > 0:
            return "PENDING_SOON"
        else:
            return "OVERDUE"

    @property
    def is_period_only(self):
        """Verifica si es solo un período creado sin información de pago"""
        return self.status == self.StatusChoices.PERIOD_CREATED
    
    @property
    def is_paid_period(self):
        """Verifica si es un período con pago completado"""
        return self.status == self.StatusChoices.PAID
    
    @property
    def can_be_paid(self):
        """Verifica si el período puede recibir un pago"""
        return self.status in [
            self.StatusChoices.PERIOD_CREATED,
            self.StatusChoices.PENDING
        ]
    
    @property
    def has_payment_info(self):
        """Verifica si tiene información de pago completa"""
        return all([
            self.amount is not None,
            self.payment_date is not None,
            self.payment_method is not None
        ])

    def mark_as_paid(self, payment_date=None, payment_method=None, reference_number=None):
        self.status = self.StatusChoices.PAID
        if payment_date:
            self.payment_date = payment_date
        if payment_method:
            self.payment_method = payment_method
        if reference_number:
            self.reference_number = reference_number
        self.save()

    def mark_as_overdue(self):
        if self.status == self.StatusChoices.PENDING:
            self.status = self.StatusChoices.OVERDUE
            self.save()

    def cancel(self, reason=None):
        self.status = self.StatusChoices.CANCELLED
        if reason:
            self.notes = f"{self.notes}\nCancelado: {reason}" if self.notes else f"Cancelado: {reason}"
        self.save()

    def refund(self, reason=None):
        if self.status == self.StatusChoices.PAID:
            self.status = self.StatusChoices.REFUNDED
            if reason:
                self.notes = f"{self.notes}\nReembolsado: {reason}" if self.notes else f"Reembolsado: {reason}"
            self.save()

    def get_payment_timing_analysis(self):
        from .services.payment_service import PaymentService
        return PaymentService.analyze_payment_timing(self)
