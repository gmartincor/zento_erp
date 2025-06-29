from django.contrib import admin
from django.utils.html import format_html
from .models import BusinessLine
from .models_remanentes import RemanenteType, BusinessLineRemanenteConfig, ServicePeriodRemanente


class BusinessLineRemanenteConfigInline(admin.TabularInline):
    model = BusinessLineRemanenteConfig
    extra = 0
    fields = ['remanente_type', 'is_enabled', 'default_amount']
    autocomplete_fields = ['remanente_type']


@admin.register(BusinessLine)
class BusinessLineAdmin(admin.ModelAdmin):
    """
    Admin interface for BusinessLine with flexible remanentes system.
    """
    list_display = ['name', 'parent', 'level', 'allows_remanentes', 'remanente_types_display', 'is_active', 'order']
    list_filter = ['level', 'allows_remanentes', 'is_active', 'parent']
    search_fields = ['name', 'slug']
    ordering = ['level', 'order', 'name']
    readonly_fields = ['slug', 'level']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'parent', 'slug', 'level', 'is_active', 'order')
        }),
        ('Configuración de Remanentes', {
            'fields': ('allows_remanentes',),
            'description': 'Configure si esta línea de negocio puede tener remanentes asociados'
        }),
    )
    
    inlines = [BusinessLineRemanenteConfigInline]
    
    def remanente_types_display(self, obj):
        """Muestra los tipos de remanente configurados para esta línea"""
        if not obj.allows_remanentes:
            return format_html('<span style="color: #999;">Sin remanentes</span>')
        
        types = obj.get_available_remanente_types()
        if not types:
            return format_html('<span style="color: #ff6b6b;">Sin tipos configurados</span>')
        
        type_names = [t.name for t in types]
        return format_html('<span style="color: #51cf66;">{}</span>', ', '.join(type_names))
    
    remanente_types_display.short_description = 'Tipos de Remanente'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('remanente_configs__remanente_type')


@admin.register(RemanenteType)
class RemanenteTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'default_amount', 'is_active', 'business_lines_count', 'created_by', 'created']
    list_filter = ['is_active', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['created_by', 'created', 'modified']
    
    fieldsets = (
        ('Información del Tipo', {
            'fields': ('name', 'description', 'default_amount', 'is_active')
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created', 'modified'),
            'classes': ('collapse',)
        })
    )
    
    def business_lines_count(self, obj):
        """Número de líneas de negocio que usan este tipo"""
        count = obj.businesslineremanenteconfig_set.filter(is_enabled=True).count()
        return f"{count} líneas"
    
    business_lines_count.short_description = 'Líneas que lo usan'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BusinessLineRemanenteConfig)
class BusinessLineRemanenteConfigAdmin(admin.ModelAdmin):
    list_display = ['business_line', 'remanente_type', 'is_enabled', 'effective_default_amount']
    list_filter = ['is_enabled', 'remanente_type', 'business_line__level']
    search_fields = ['business_line__name', 'remanente_type__name']
    autocomplete_fields = ['business_line', 'remanente_type']
    
    def effective_default_amount(self, obj):
        """Muestra el monto por defecto efectivo"""
        amount = obj.get_effective_default_amount()
        if amount:
            return f"€{amount}"
        return "Sin monto"
    
    effective_default_amount.short_description = 'Monto Efectivo'


@admin.register(ServicePeriodRemanente)
class ServicePeriodRemanenteAdmin(admin.ModelAdmin):
    list_display = ['client_service_display', 'period_start', 'period_end', 'remanente_type', 'amount', 'created_by']
    list_filter = ['remanente_type', 'created_by', 'period_start']
    search_fields = ['client_service__client__full_name', 'client_service__business_line__name']
    readonly_fields = ['created_by', 'created', 'modified']
    date_hierarchy = 'period_start'
    
    fieldsets = (
        ('Información del Remanente', {
            'fields': ('client_service', 'remanente_type', 'amount')
        }),
        ('Período', {
            'fields': ('period_start', 'period_end')
        }),
        ('Detalles', {
            'fields': ('notes', 'created_by', 'created', 'modified'),
            'classes': ('collapse',)
        })
    )
    
    def client_service_display(self, obj):
        """Representación clara del servicio"""
        return f"{obj.client_service.client.full_name} - {obj.client_service.business_line.name}"
    
    client_service_display.short_description = 'Cliente y Servicio'
    client_service_display.admin_order_field = 'client_service__client__full_name'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
