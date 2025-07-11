from django.contrib import admin
from .models import Company, Invoice, VATRate, IRPFRate


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'entity_type', 'tax_id', 'city']
    list_filter = ['entity_type']
    search_fields = ['business_name', 'tax_id']
    fieldsets = (
        ('Información básica', {
            'fields': ('entity_type', 'business_name', 'legal_name', 'tax_id')
        }),
        ('Dirección', {
            'fields': ('address', 'postal_code', 'city')
        }),
        ('Contacto', {
            'fields': ('phone', 'email')
        }),
        ('Datos bancarios', {
            'fields': ('bank_name', 'iban')
        }),
        ('Configuración fiscal', {
            'fields': ('default_vat_rate', 'irpf_rate')
        }),
        ('Configuración de facturas', {
            'fields': ('invoice_prefix', 'current_number', 'logo')
        }),
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['reference', 'client_name', 'issue_date', 'total_amount', 'status']
    list_filter = ['status', 'client_type', 'issue_date', 'vat_rate', 'irpf_rate']
    search_fields = ['reference', 'client_name', 'client_tax_id']
    readonly_fields = ['reference', 'base_amount', 'vat_amount', 'irpf_amount', 'total_amount']
    date_hierarchy = 'issue_date'
    
    fieldsets = (
        ('Información de la factura', {
            'fields': ('reference', 'issue_date', 'status')
        }),
        ('Cliente', {
            'fields': ('client_type', 'client_name', 'client_tax_id', 'client_address')
        }),
        ('Servicio', {
            'fields': ('service_description', 'quantity', 'unit_price')
        }),
        ('Impuestos', {
            'fields': ('vat_rate', 'irpf_rate')
        }),
        ('Totales', {
            'fields': ('base_amount', 'vat_amount', 'irpf_amount', 'total_amount'),
            'classes': ('collapse',)
        }),
        ('Condiciones de pago', {
            'fields': ('payment_terms',)
        }),
        ('Archivo PDF', {
            'fields': ('pdf_file',)
        }),
    )


@admin.register(VATRate)
class VATRateAdmin(admin.ModelAdmin):
    list_display = ['name', 'rate', 'is_default']
    list_filter = ['is_default']
    search_fields = ['name']
    ordering = ['rate']


@admin.register(IRPFRate)
class IRPFRateAdmin(admin.ModelAdmin):
    list_display = ['name', 'rate', 'is_default']
    list_filter = ['is_default']
    search_fields = ['name']
    ordering = ['rate']
