from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel, SoftDeleteModel
from apps.business_lines.models import BusinessLine


class Client(TimeStampedModel, SoftDeleteModel):
    """
    Client model for managing customer information.
    """
    
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
    """
    Links clients to business lines with service details.
    """
    
    class CategoryChoices(models.TextChoices):
        WHITE = 'WHITE', 'Blanco'
        BLACK = 'BLACK', 'Negro'
    
    class PaymentMethodChoices(models.TextChoices):
        CARD = 'CARD', 'Tarjeta'
        CASH = 'CASH', 'Efectivo'
        TRANSFER = 'TRANSFER', 'Transferencia'
        BIZUM = 'BIZUM', 'Bizum'
    
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
        verbose_name="Precio"
    )
    
    payment_method = models.CharField(
        max_length=15,
        choices=PaymentMethodChoices.choices,
        verbose_name="Método de pago"
    )
    
    start_date = models.DateField(
        verbose_name="Fecha de inicio"
    )
    
    renewal_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de renovación"
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

    class Meta:
        db_table = 'client_services'
        verbose_name = "Servicio de cliente"
        verbose_name_plural = "Servicios de clientes"
        unique_together = [['client', 'business_line', 'category']]
        indexes = [
            models.Index(fields=['client', 'is_active']),
            models.Index(fields=['business_line', 'category']),
            models.Index(fields=['start_date']),
        ]

    def clean(self):
        """
        Validate that remanentes are only used for BLACK category and match the business line's remanente_field.
        """
        super().clean()
        
        # Validate category
        if self.category != self.CategoryChoices.BLACK and self.remanentes:
            raise ValidationError({
                'remanentes': 'Los remanentes solo pueden configurarse para la categoría BLACK.'
            })
        
        # Validate remanentes structure
        if self.category == self.CategoryChoices.BLACK and not isinstance(self.remanentes, dict):
            raise ValidationError({
                'remanentes': 'Los remanentes deben ser un diccionario válido para la categoría BLACK.'
            })
        
        # Validate business line and remanente_field relationship
        if self.category == self.CategoryChoices.BLACK:
            # Skip validation if business_line is None (can happen during form validation before saving)
            if not self.business_line_id:
                return
            
            # Validate that the business line has a remanente_field configured
            if not self.business_line.has_remanente or not self.business_line.remanente_field:
                raise ValidationError({
                    'business_line': f'La línea de negocio "{self.business_line.name}" no tiene un tipo de remanente configurado.'
                })
            
            # Validate specific business lines to remanente_field mappings
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
            
            # Validate that the remanentes JSON only contains valid keys for the business line's remanente_field
            if self.remanentes and isinstance(self.remanentes, dict):
                valid_keys = {self.business_line.remanente_field}
                invalid_keys = set(self.remanentes.keys()) - valid_keys
                
                if invalid_keys:
                    raise ValidationError({
                        'remanentes': f'El campo de remanentes contiene claves no válidas para esta línea de negocio: {", ".join(invalid_keys)}. '
                                     f'Solo se permite la clave "{self.business_line.remanente_field}" para la línea "{self.business_line.name}".'
                    })

    def save(self, *args, **kwargs):
        """
        Custom save method to validate remanentes for BLACK category.
        """
        # Clear remanentes if not BLACK category
        if self.category != self.CategoryChoices.BLACK:
            self.remanentes = {}
        
        # Ensure remanentes is a dict for BLACK category
        elif self.category == self.CategoryChoices.BLACK and not isinstance(self.remanentes, dict):
            self.remanentes = {}
        
        # Format remanentes to only contain valid keys for the business line's remanente_field
        elif self.category == self.CategoryChoices.BLACK and self.business_line_id and self.business_line.remanente_field:
            # Filter remanentes to only include the valid key for this business line
            valid_key = self.business_line.remanente_field
            if valid_key in self.remanentes:
                valid_value = self.remanentes[valid_key]
                self.remanentes = {valid_key: valid_value}
            else:
                self.remanentes = {}
        
        # Call clean method for validation
        self.clean()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client.full_name} - {self.business_line.name} ({self.category})"

    def get_remanente_total(self):
        """
        Calculate total remanente amount for BLACK category.
        """
        if self.category == self.CategoryChoices.BLACK and self.remanentes:
            return sum(float(value) for value in self.remanentes.values() if isinstance(value, (int, float, str)) and str(value).replace('.', '').isdigit())
        return 0
