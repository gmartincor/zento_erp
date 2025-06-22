from django.contrib import admin
from django.utils.html import format_html
from .models import Client, ClientService


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    
    list_display = [
        'full_name',
        'dni',
        'gender',
        'email',
        'phone',
        'is_active',
        'created',
        'is_deleted'
    ]
    
    list_filter = [
        'is_active',
        'gender',
        'is_deleted',
        'created'
    ]
    
    search_fields = [
        'full_name',
        'dni',
        'email'
    ]
    
    list_editable = ['is_active']
    
    ordering = ['-created']
    
    readonly_fields = ['created', 'modified', 'deleted_at']
    
    fieldsets = (
        ('Información personal', {
            'fields': ('full_name', 'dni', 'gender')
        }),
        ('Contacto', {
            'fields': ('email', 'phone')
        }),
        ('Información adicional', {
            'fields': ('notes', 'is_active')
        }),
        ('Control de eliminación', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(ClientService)
class ClientServiceAdmin(admin.ModelAdmin):
    
    list_display = [
        'client_name_display',
        'business_line',
        'category',
        'price',
        'payment_method',
        'start_date',
        'renewal_date',
        'is_active'
    ]
    
    list_filter = [
        'category',
        'business_line',
        'payment_method',
        'is_active',
        'created'
    ]
    
    search_fields = [
        'client__full_name',
        'client__dni',
        'business_line__name'
    ]
    
    list_editable = ['is_active']
    
    date_hierarchy = 'renewal_date'
    
    ordering = ['-renewal_date', '-created']
    
    readonly_fields = ['created', 'modified']
    
    autocomplete_fields = ['client']
    
    fieldsets = (
        ('Relaciones', {
            'fields': ('client', 'business_line')
        }),
        ('Detalles del servicio', {
            'fields': ('category', 'price', 'payment_method')
        }),
        ('Fechas', {
            'fields': ('start_date', 'renewal_date')
        }),
        ('Remanentes', {
            'fields': ('remanentes',),
            'classes': ('collapse',),
            'description': 'Solo aplicable para categoría BLACK'
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('client', 'business_line')

    def client_name_display(self, obj):
        status_icon = '✓' if obj.client.is_active else '✗'
        status_color = 'green' if obj.client.is_active else 'red'
        
        return format_html(
            '<span style="color: {};">{}</span> {} ({})',
            status_color,
            status_icon,
            obj.client.full_name,
            obj.client.dni
        )
    
    client_name_display.short_description = 'Cliente'
    client_name_display.admin_order_field = 'client__full_name'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        if 'remanentes' in form.base_fields:
            form.base_fields['remanentes'].help_text = (
                'Formato JSON. Solo válido para categoría BLACK. '
                'Cada línea de negocio solo acepta su tipo específico de remanente. Ejemplos:<br>'
                '- PEPE-normal: {"remanente_pepe": 100.50}<br>'
                '- PEPE-videoCall: {"remanente_pepe_video": 75.25}<br>'
                '- Dani-Rubi: {"remanente_dani": 50.00}<br>'
                '- Dani: {"remanente_aven": 120.00}'
            )
        
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


class ClientAdmin(ClientAdmin):
    search_fields = ['full_name', 'dni', 'email']
