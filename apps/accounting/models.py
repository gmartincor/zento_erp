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


class ClientService(TimeStampedModel):
    
    class CategoryChoices(models.TextChoices):
        WHITE = 'WHITE', 'Blanco'
        BLACK = 'BLACK', 'Negro'
    
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
        unique_together = [['client', 'business_line', 'category']]
        indexes = [
            models.Index(fields=['client', 'is_active']),
            models.Index(fields=['business_line', 'category']),
        ]

    def clean(self):
        super().clean()
        
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
    
    def get_line_path(self):
        return self.business_line.get_url_path()

    @property
    def current_status(self):
        latest_payment = self.payments.filter(status=ServicePayment.StatusChoices.PAID).order_by('-period_end').first()
        if not latest_payment:
            return 'INACTIVE'
        
        today = timezone.now().date()
        if latest_payment.period_end >= today:
            return 'ACTIVE'
        elif (today - latest_payment.period_end).days <= 30:
            return 'EXPIRED_RECENT'
        else:
            return 'EXPIRED'

    @property
    def active_until(self):
        latest_payment = self.payments.filter(status=ServicePayment.StatusChoices.PAID).order_by('-period_end').first()
        return latest_payment.period_end if latest_payment else None

    @property
    def total_paid(self):
        return self.payments.filter(status=ServicePayment.StatusChoices.PAID).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

    @property
    def payment_count(self):
        return self.payments.filter(status=ServicePayment.StatusChoices.PAID).count()

    @property
    def current_amount(self):
        """Get the amount of the latest payment (current pricing)"""
        latest_payment = self.payments.order_by('-created').first()
        return latest_payment.amount if latest_payment else 0

    @property
    def current_payment_method(self):
        """Get the payment method of the latest payment"""
        latest_payment = self.payments.order_by('-created').first()
        return latest_payment.payment_method if latest_payment else None

    def get_payment_method_display(self):
        """Get the display name of the current payment method"""
        method = self.current_payment_method
        if not method:
            return "No definido"
        
        # Import ServicePayment here to avoid circular imports
        payment_choices = dict(ServicePayment.PaymentMethodChoices.choices)
        return payment_choices.get(method, method)

    @property
    def current_start_date(self):
        """Get the start date of the latest payment"""
        latest_payment = self.payments.order_by('-created').first()
        return latest_payment.period_start if latest_payment else None

    @property
    def current_end_date(self):
        """Get the end date of the latest payment"""
        latest_payment = self.payments.order_by('-created').first()
        return latest_payment.period_end if latest_payment else None


class ServicePayment(TimeStampedModel):
    
    class StatusChoices(models.TextChoices):
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
        verbose_name="Monto"
    )
    
    payment_date = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de pago"
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
        default=StatusChoices.PENDING,
        verbose_name="Estado"
    )
    
    payment_method = models.CharField(
        max_length=15,
        choices=PaymentMethodChoices.choices,
        verbose_name="Método de pago"
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
