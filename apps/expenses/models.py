from django.db import models
from django.utils.text import slugify
from apps.core.models import TimeStampedModel
import os


def expense_attachment_path(instance, filename):
    year = instance.date.year
    month = instance.date.month
    return f'expenses/{year}/{month:02d}/{filename}'


class ExpenseCategory(TimeStampedModel):
    
    class CategoryTypeChoices(models.TextChoices):
        FIXED = 'FIXED', 'Fijo'
        VARIABLE = 'VARIABLE', 'Variable'
        TAX = 'TAX', 'Impuesto'
        OCCASIONAL = 'OCCASIONAL', 'Puntual'
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre"
    )
    
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="Slug"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Descripción"
    )
    
    category_type = models.CharField(
        max_length=20,
        choices=CategoryTypeChoices.choices,
        verbose_name="Tipo de categoría"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        db_index=True
    )

    class Meta:
        db_table = 'expense_categories'
        verbose_name = "Categoría de gasto"
        verbose_name_plural = "Categorías de gastos"
        ordering = ['category_type', 'name']
        indexes = [
            models.Index(fields=['category_type', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class Expense(TimeStampedModel):
    
    class ServiceCategoryChoices(models.TextChoices):
        PERSONAL = 'personal', 'Personal'
        BUSINESS = 'business', 'Business'
    
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name='expenses',
        verbose_name="Categoría"
    )
    
    service_category = models.CharField(
        max_length=10,
        choices=ServiceCategoryChoices.choices,
        default=ServiceCategoryChoices.BUSINESS,
        verbose_name="Categoría de Servicio"
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importe"
    )
    
    date = models.DateField(
        verbose_name="Fecha"
    )
    
    description = models.TextField(
        verbose_name="Descripción"
    )
    
    accounting_year = models.PositiveIntegerField(
        verbose_name="Año contable",
        db_index=True
    )
    
    accounting_month = models.PositiveSmallIntegerField(
        verbose_name="Mes contable",
        db_index=True
    )
    
    invoice_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Número de factura"
    )
    
    attachment = models.FileField(
        upload_to=expense_attachment_path,
        blank=True,
        null=True,
        verbose_name="Archivo adjunto"
    )

    class Meta:
        db_table = 'expenses'
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        ordering = ['-date', '-created']
        indexes = [
            models.Index(fields=['accounting_year', 'accounting_month']),
            models.Index(fields=['category', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['accounting_year', 'category']),
            models.Index(fields=['service_category', 'date']),
        ]

    def save(self, *args, **kwargs):
        if self.date:
            self.accounting_year = self.date.year
            self.accounting_month = self.date.month
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} - {self.amount}€ ({self.date})"

    def get_attachment_filename(self):
        if self.attachment:
            return os.path.basename(self.attachment.name)
        return None
