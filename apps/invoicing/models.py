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
        return self.legal_form == 'AUTONOMO'
    
    @property 
    def is_company(self):
        return self.legal_form != 'AUTONOMO'

    def __str__(self):
        return self.business_name

    class Meta:
        verbose_name_plural = "Companies"


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
    issue_date = models.DateField(default=date.today, verbose_name="Fecha de emisión")
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPES, verbose_name="Tipo de cliente")
    client_name = models.CharField(max_length=200, verbose_name="Nombre del cliente")
    client_tax_id = models.CharField(max_length=15, blank=True, verbose_name="NIF/CIF del cliente")
    client_address = models.TextField(verbose_name="Dirección del cliente")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    payment_terms = models.TextField(default="Transferencia bancaria", verbose_name="Condiciones de pago")
    pdf_file = models.FileField(upload_to='invoices/pdfs/', blank=True)

    @property
    def base_amount(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def vat_amount(self):
        return sum(item.vat_amount for item in self.items.all())

    @property
    def irpf_amount(self):
        return sum(item.irpf_amount for item in self.items.all())

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
        if any(item.vat_rate == 0 for item in self.items.all()):
            return "Exenta de IVA según el artículo correspondiente de la Ley del IVA."
        return ""

    def save(self, *args, **kwargs):
        if not self.reference and self.company:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} - {self.client_name}"

    class Meta:
        ordering = ['-issue_date']


class InvoiceItem(models.Model):
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='items')
    description = models.TextField(verbose_name="Descripción")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Precio unitario"
    )
    vat_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=21.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="IVA (%)"
    )
    irpf_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="IRPF (%)"
    )
    
    @property
    def line_total(self):
        return self.quantity * self.unit_price
    
    @property
    def vat_amount(self):
        return self.line_total * self.vat_rate / 100
    
    @property
    def irpf_amount(self):
        return self.line_total * self.irpf_rate / 100
    
    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.unit_price}€"
