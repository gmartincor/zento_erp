from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Client, ClientService, ServicePayment


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
        'current_status_display',
        'payment_count_display',
        'total_paid_display',
        'active_until_display',
        'is_active'
    ]
    
    list_filter = [
        'category',
        'business_line',
        'is_active',
        'created'
    ]
    
    search_fields = [
        'client__full_name',
        'client__dni',
        'business_line__name'
    ]
    
    list_editable = ['is_active']
    
    ordering = ['-created']
    
    readonly_fields = ['created', 'modified', 'current_status_display', 'payment_count_display', 'total_paid_display']
    
    autocomplete_fields = ['client']
    
    fieldsets = (
        ('Relaciones', {
            'fields': ('client', 'business_line')
        }),
        ('Detalles del servicio', {
            'fields': ('category',)
        }),
        ('Remanentes', {
            'fields': ('remanentes',),
            'classes': ('collapse',),
            'description': 'Solo aplicable para categoría BLACK'
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Información de pagos', {
            'fields': ('current_status_display', 'payment_count_display', 'total_paid_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('client', 'business_line').prefetch_related('payments')

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

    def current_status_display(self, obj):
        status = obj.current_status
        status_colors = {
            'ACTIVE': 'green',
            'EXPIRED_RECENT': 'orange',
            'EXPIRED': 'red',
            'INACTIVE': 'gray'
        }
        status_labels = {
            'ACTIVE': 'Activo',
            'EXPIRED_RECENT': 'Vencido reciente',
            'EXPIRED': 'Vencido',
            'INACTIVE': 'Inactivo'
        }
        
        color = status_colors.get(status, 'black')
        label = status_labels.get(status, status)
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            label
        )
    
    current_status_display.short_description = 'Estado actual'

    def payment_count_display(self, obj):
        count = obj.payment_count
        return format_html('<strong>{}</strong> pagos', count)
    
    payment_count_display.short_description = 'Pagos realizados'

    def total_paid_display(self, obj):
        total = obj.total_paid
        return format_html('<strong>{:.2f}€</strong>', total)
    
    total_paid_display.short_description = 'Total pagado'

    def active_until_display(self, obj):
        date = obj.active_until
        if date:
            return format_html('<strong>{}</strong>', date.strftime('%d/%m/%Y'))
        return '-'
    
    active_until_display.short_description = 'Activo hasta'

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


class ServicePaymentInline(admin.TabularInline):
    model = ServicePayment
    extra = 0
    readonly_fields = ['created', 'duration_days', 'is_active_period']
    fields = ['payment_date', 'amount', 'period_start', 'period_end', 'status', 'payment_method', 'reference_number']
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-payment_date')


@admin.register(ServicePayment)
class ServicePaymentAdmin(admin.ModelAdmin):
    
    list_display = [
        'client_service_display',
        'amount_display',
        'payment_date',
        'period_display',
        'status_display',
        'payment_method',
        'reference_number'
    ]
    
    list_filter = [
        'status',
        'payment_method',
        'payment_date',
        'period_start',
        'period_end'
    ]
    
    search_fields = [
        'client_service__client__full_name',
        'client_service__client__dni',
        'client_service__business_line__name',
        'reference_number'
    ]
    
    date_hierarchy = 'payment_date'
    
    ordering = ['-payment_date', '-created']
    
    readonly_fields = ['created', 'modified', 'duration_days', 'is_active_period', 'days_until_expiry']
    
    autocomplete_fields = ['client_service']
    
    fieldsets = (
        ('Información del pago', {
            'fields': ('client_service', 'amount', 'payment_date', 'payment_method', 'reference_number')
        }),
        ('Período cubierto', {
            'fields': ('period_start', 'period_end', 'duration_days', 'is_active_period', 'days_until_expiry')
        }),
        ('Estado', {
            'fields': ('status',)
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'client_service__client',
            'client_service__business_line'
        )

    def client_service_display(self, obj):
        return format_html(
            '{} - {} ({})',
            obj.client_service.client.full_name,
            obj.client_service.business_line.name,
            obj.client_service.get_category_display()
        )
    
    client_service_display.short_description = 'Servicio'
    client_service_display.admin_order_field = 'client_service__client__full_name'

    def amount_display(self, obj):
        return format_html('<strong>{:.2f}€</strong>', obj.amount)
    
    amount_display.short_description = 'Monto'
    amount_display.admin_order_field = 'amount'

    def period_display(self, obj):
        return format_html(
            '{} - {} ({} días)',
            obj.period_start.strftime('%d/%m/%Y'),
            obj.period_end.strftime('%d/%m/%Y'),
            obj.duration_days
        )
    
    period_display.short_description = 'Período'

    def status_display(self, obj):
        status_colors = {
            'PENDING': 'orange',
            'PAID': 'green',
            'OVERDUE': 'red',
            'CANCELLED': 'gray',
            'REFUNDED': 'blue'
        }
        
        color = status_colors.get(obj.status, 'black')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    status_display.short_description = 'Estado'
    status_display.admin_order_field = 'status'

    actions = ['mark_as_paid', 'mark_as_overdue', 'cancel_payments']

    def mark_as_paid(self, request, queryset):
        count = 0
        for payment in queryset:
            if payment.status == ServicePayment.StatusChoices.PENDING:
                payment.mark_as_paid()
                count += 1
        
        self.message_user(request, f'{count} pagos marcados como pagados.')
    
    mark_as_paid.short_description = 'Marcar como pagado'

    def mark_as_overdue(self, request, queryset):
        count = 0
        for payment in queryset:
            if payment.status == ServicePayment.StatusChoices.PENDING:
                payment.mark_as_overdue()
                count += 1
        
        self.message_user(request, f'{count} pagos marcados como vencidos.')
    
    mark_as_overdue.short_description = 'Marcar como vencido'

    def cancel_payments(self, request, queryset):
        count = 0
        for payment in queryset:
            if payment.status in [ServicePayment.StatusChoices.PENDING, ServicePayment.StatusChoices.OVERDUE]:
                payment.cancel('Cancelado desde admin')
                count += 1
        
        self.message_user(request, f'{count} pagos cancelados.')
    
    cancel_payments.short_description = 'Cancelar pagos'


admin.site.unregister(ClientService)
admin.site.register(ClientService, ClientServiceAdmin)


class ClientServiceInline(admin.TabularInline):
    model = ClientService
    extra = 0
    fields = ['business_line', 'category', 'is_active']
    readonly_fields = ['created']
