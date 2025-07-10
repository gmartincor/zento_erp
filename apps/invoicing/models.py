from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.core.models import TimeStampedModel


class Company(TimeStampedModel):
    ENTITY_TYPES = [
        ('COMPANY', 'Empresa'),
        ('FREELANCER', 'Autónomo'),
    ]
    
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    business_name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=15)
    address = models.TextField()
    postal_code = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    bank_name = models.CharField(max_length=100)
    iban = models.CharField(max_length=34)
    default_vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=21.00)
    irpf_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    invoice_prefix = models.CharField(max_length=10, default="FN")
    current_number = models.IntegerField(default=0)

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
    reference = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField()
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPES)
    client_name = models.CharField(max_length=200)
    client_tax_id = models.CharField(max_length=15, blank=True)
    client_address = models.TextField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    irpf_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    payment_terms = models.TextField(default="Transferencia bancaria")
    pdf_file = models.FileField(upload_to='invoices/pdfs/', blank=True)

    def generate_reference(self):
        if not self.issue_date:
            from datetime import date
            self.issue_date = date.today()
        year = self.issue_date.year % 100
        self.company.current_number += 1
        self.company.save()
        return f"{self.company.invoice_prefix}{self.company.current_number:03d}_{year}"

    def calculate_totals(self):
        subtotal = sum(line.line_total for line in self.lines.all())
        vat_amount = sum(line.line_total * line.vat_rate / 100 for line in self.lines.all())
        
        irpf_amount = 0
        if (self.company.entity_type == 'FREELANCER' and 
            self.client_type == 'COMPANY' and 
            subtotal > 300):
            irpf_amount = subtotal * self.company.irpf_rate / 100
        
        total_amount = subtotal + vat_amount - irpf_amount
        
        self.subtotal = subtotal
        self.vat_amount = vat_amount
        self.irpf_amount = irpf_amount
        self.total_amount = total_amount
        self.save()

    def __str__(self):
        return f"{self.reference} - {self.client_name}"

    class Meta:
        ordering = ['-issue_date']


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='lines', on_delete=models.CASCADE)
    description = models.TextField()
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=21.00)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        if self.invoice_id:
            self.invoice.calculate_totals()

    def __str__(self):
        return f"{self.description} - {self.line_total}€"


@receiver(post_save, sender=InvoiceLine)
def recalculate_invoice_totals_on_save(sender, instance, **kwargs):
    if instance.invoice_id:
        instance.invoice.calculate_totals()


@receiver(post_delete, sender=InvoiceLine)
def recalculate_invoice_totals_on_delete(sender, instance, **kwargs):
    if instance.invoice_id:
        instance.invoice.calculate_totals()
