from django.contrib import admin
from .models import Company, Invoice, InvoiceLine


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'entity_type', 'tax_id', 'city']
    list_filter = ['entity_type']
    search_fields = ['business_name', 'tax_id']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['reference', 'client_name', 'issue_date', 'total_amount', 'status']
    list_filter = ['status', 'client_type', 'issue_date']
    search_fields = ['reference', 'client_name', 'client_tax_id']
    readonly_fields = ['reference', 'subtotal', 'vat_amount', 'irpf_amount', 'total_amount']
    inlines = [InvoiceLineInline]
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.reference = obj.generate_reference()
        super().save_model(request, obj, form, change)


@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'unit_price', 'line_total']
    list_filter = ['vat_rate']
