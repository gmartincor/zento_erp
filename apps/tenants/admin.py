from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from apps.core.constants import TENANT_SUCCESS_MESSAGES
from .models import Tenant
from .forms import TenantUpdateForm, TenantStatusForm
from .services import TenantService


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    form = TenantUpdateForm
    
    list_display = [
        'name',
        'email',
        'slug',
        'status_badge',
        'is_active',
        'created',
        'formatted_url',
        'action_links'
    ]
    
    list_filter = [
        'status',
        'is_active',
        'is_deleted',
        'created',
        'modified'
    ]
    
    search_fields = [
        'name',
        'email',
        'slug',
        'professional_number'
    ]
    
    list_editable = ['is_active']
    
    ordering = ['-created']
    
    readonly_fields = [
        'created',
        'modified',
        'deleted_at',
        'formatted_url_link',
        'tenant_stats'
    ]
    
    fieldsets = (
        ('Información del Nutricionista', {
            'fields': ('name', 'email', 'phone', 'professional_number')
        }),
        ('Configuración', {
            'fields': ('slug', 'formatted_url_link')
        }),
        ('Estado y Control', {
            'fields': ('status', 'is_active', 'notes')
        }),
        ('Información del Sistema', {
            'fields': ('created', 'modified', 'is_deleted', 'deleted_at', 'tenant_stats'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_tenants', 'suspend_tenants', 'restore_tenants']
    
    def get_queryset(self, request):
        return Tenant.all_objects.all()
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#ffc107',
            'ACTIVE': '#28a745',
            'SUSPENDED': '#fd7e14',
            'INACTIVE': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def formatted_url(self, obj):
        return obj.full_url
    formatted_url.short_description = 'URL'
    
    def formatted_url_link(self, obj):
        if obj.pk:
            full_url = f"http://localhost:8000{obj.full_url}"
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                full_url,
                full_url
            )
        return '-'
    formatted_url_link.short_description = 'URL de Acceso'
    
    def action_links(self, obj):
        if not obj.pk:
            return '-'
        
        links = []
        
        if obj.status == Tenant.StatusChoices.PENDING:
            links.append(f'<a href="#" onclick="activateTenant({obj.pk})">Activar</a>')
        
        if obj.status == Tenant.StatusChoices.ACTIVE:
            links.append(f'<a href="#" onclick="suspendTenant({obj.pk})">Suspender</a>')
        
        if obj.is_deleted:
            links.append(f'<a href="#" onclick="restoreTenant({obj.pk})">Restaurar</a>')
        
        return mark_safe(' | '.join(links)) if links else '-'
    action_links.short_description = 'Acciones'
    
    def tenant_stats(self, obj):
        if not obj.pk or not obj.is_available:
            return 'N/A'
        
        try:
            from .services import TenantDataService
            
            def get_stats():
                from apps.accounting.models import Client
                from apps.business_lines.models import BusinessLine
                
                return {
                    'clients': Client.objects.count(),
                    'business_lines': BusinessLine.objects.count()
                }
            
            stats = TenantDataService.execute_in_tenant_context(obj, get_stats)
            
            return format_html(
                'Clientes: {} | Líneas de negocio: {}',
                stats['clients'],
                stats['business_lines']
            )
        except Exception:
            return 'Error obteniendo estadísticas'
    tenant_stats.short_description = 'Estadísticas'
    
    def activate_tenants(self, request, queryset):
        count = 0
        for tenant in queryset:
            try:
                TenantService.activate_tenant(tenant.id)
                count += 1
            except Exception:
                pass
        
        self.message_user(
            request,
            f"{count} tenants activados exitosamente.",
            messages.SUCCESS
        )
    activate_tenants.short_description = "Activar tenants seleccionados"
    
    def suspend_tenants(self, request, queryset):
        count = 0
        for tenant in queryset:
            try:
                TenantService.suspend_tenant(tenant.id, "Suspendido desde admin")
                count += 1
            except Exception:
                pass
        
        self.message_user(
            request,
            f"{count} tenants suspendidos exitosamente.",
            messages.WARNING
        )
    suspend_tenants.short_description = "Suspender tenants seleccionados"
    
    def restore_tenants(self, request, queryset):
        count = 0
        for tenant in queryset.filter(is_deleted=True):
            try:
                tenant.restore()
                count += 1
            except Exception:
                pass
        
        self.message_user(
            request,
            f"{count} tenants restaurados exitosamente.",
            messages.SUCCESS
        )
    restore_tenants.short_description = "Restaurar tenants eliminados"
