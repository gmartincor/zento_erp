from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from apps.core.models import TimeStampedModel
from django.conf import settings


class Company(TimeStampedModel):
    LEGAL_FORMS = [
        ('AUTONOMO', 'Autónomo/a'),
        ('SL', 'Sociedad Limitada (SL)'),
        ('SA', 'Sociedad Anónima (SA)'),
        ('SLU', 'Sociedad Limitada Unipersonal (SLU)'),
        ('SCP', 'Sociedad Civil Privada (SCP)'),
        ('CB', 'Comunidad de Bienes (CB)'),
    ]
    
    # Campo unificado que sustituye a entity_type
    legal_form = models.CharField(max_length=20, choices=LEGAL_FORMS, verbose_name="Forma jurídica")
    business_name = models.CharField(max_length=200, verbose_name="Nombre comercial")
    legal_name = models.CharField(max_length=200, blank=True, verbose_name="Razón social")
    tax_id = models.CharField(max_length=15, verbose_name="NIF/CIF")
    address = models.TextField(verbose_name="Dirección")
    postal_code = models.CharField(max_length=10, verbose_name="Código postal")
    city = models.CharField(max_length=100, verbose_name="Ciudad")
    province = models.CharField(max_length=100, blank=True, verbose_name="Provincia")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    bank_name = models.CharField(max_length=100, verbose_name="Banco")
    iban = models.CharField(max_length=34, verbose_name="IBAN")
    mercantile_registry = models.CharField(max_length=200, blank=True, verbose_name="Registro Mercantil")
    share_capital = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Capital social")
    default_vat_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=21.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Tipo de IVA por defecto"
    )
    irpf_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=15.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Tipo de IRPF por defecto"
    )
    invoice_prefix = models.CharField(max_length=10, default="FN", verbose_name="Prefijo de factura")
    current_number = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    logo = models.ImageField(upload_to='company/logos/', blank=True, null=True)

    def get_full_address(self):
        return f"{self.address}, {self.postal_code} {self.city}"

    def get_display_name(self):
        return self.legal_name or self.business_name

    def save(self, *args, **kwargs):
        if not self.pk and Company.objects.exists():
            raise ValidationError('Solo puede existir una empresa por tenant.')
        super().save(*args, **kwargs)

    @property
    def is_freelancer(self):
        """Determina si la empresa es un autónomo para cálculo de IRPF"""
        return self.legal_form == 'AUTONOMO'
    
    @property 
    def is_company(self):
        """Determina si es una empresa (no autónomo)"""
        return self.legal_form != 'AUTONOMO'

    def __str__(self):
        return self.business_name

    class Meta:
        verbose_name_plural = "Companies"


class VATRate(models.Model):
    name = models.CharField(max_length=50)
    rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} ({self.rate}%)"

    class Meta:
        ordering = ['rate']


class IRPFRate(models.Model):
    name = models.CharField(max_length=50)
    rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} ({self.rate}%)"

    class Meta:
        ordering = ['rate']


class Invoice(TimeStampedModel):
    CLIENT_TYPES = [
        ('COMPANY', 'Empresa'),
        ('FREELANCER', 'Autónomo'),
        ('INDIVIDUAL', 'Particular'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('SENT', 'Enviada'),
        ('PAID', 'Pagada'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    reference = models.CharField(max_length=50, unique=True, blank=True)
    issue_date = models.DateField(default=date.today)
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPES)
    client_name = models.CharField(max_length=200)
    client_tax_id = models.CharField(max_length=15, blank=True)
    client_address = models.TextField()
    service_description = models.TextField(default='Servicios profesionales')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.01'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    vat_rate = models.ForeignKey(VATRate, on_delete=models.PROTECT, null=True, blank=True)
    irpf_rate = models.ForeignKey(IRPFRate, on_delete=models.PROTECT, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    payment_terms = models.TextField(default="Transferencia bancaria")
    pdf_file = models.FileField(upload_to='invoices/pdfs/', blank=True)

    @property
    def base_amount(self):
        return self.quantity * self.unit_price

    @property
    def vat_amount(self):
        if not self.vat_rate:
            return Decimal('0.00')
        return self.base_amount * self.vat_rate.rate / 100

    @property
    def irpf_amount(self):
        if not self.irpf_rate:
            return Decimal('0.00')
        
        # IRPF solo se aplica si:
        # 1. El emisor (company) es autónomo/freelancer
        # 2. El cliente es empresa 
        # 3. El importe base es mayor a 300€
        if (self.company.is_freelancer and 
            self.client_type == 'COMPANY' and 
            self.base_amount > 300):
            return self.base_amount * self.irpf_rate.rate / 100
        return Decimal('0.00')
    
    def should_apply_irpf(self):
        """Determina si debe aplicarse retención IRPF según la normativa española"""
        return (self.company.is_freelancer and 
                self.client_type == 'COMPANY' and 
                self.base_amount > 300)

    @property
    def total_amount(self):
        return self.base_amount + self.vat_amount - self.irpf_amount

    def generate_reference(self):
        if not self.issue_date:
            self.issue_date = date.today()
        year = self.issue_date.year % 100
        
        from django.db import transaction
        with transaction.atomic():
            company = Company.objects.select_for_update().get(pk=self.company.pk)
            company.current_number += 1
            company.save()
            return f"{company.invoice_prefix}{company.current_number:03d}_{year}"

    def get_legal_note(self):
        if self.vat_rate and self.vat_rate.rate == 0:
            return "Exenta de IVA según el artículo correspondiente de la Ley del IVA."
        return ""

    def clean(self):
        pass

    def save(self, *args, **kwargs):
        if not self.reference and self.company:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} - {self.client_name}"

    class Meta:
        ordering = ['-issue_date']
