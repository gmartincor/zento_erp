from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.admin import AdminSite
from apps.core.constants import TENANT_SUCCESS_MESSAGES
from apps.authentication.models import User
from .models import Tenant, Domain
from .forms import TenantAdminCreationForm, TenantUpdateForm
from .services import TenantService


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__name']


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    
    list_display = [
        'name',
        'email',
        'schema_name',
        'status_badge',
        'is_active',
        'user_info',
        'domain_info',
        'created',
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
        'schema_name',
        'professional_number'
    ]
    
    list_editable = ['is_active']
    
    ordering = ['-created']
    
    def get_readonly_fields(self, request, obj=None):
        if obj is None:  # Creación
            return ['created', 'modified', 'deleted_at', 'tenant_stats']
        else:  # Edición
            return ['created', 'modified', 'deleted_at', 'schema_name', 'tenant_stats']
    
    fieldsets = (
        ('Información del Nutricionista', {
            'fields': ('name', 'email', 'phone', 'professional_number')
        }),
        ('Configuración', {
            'fields': ('schema_name',)
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
    
    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs['form'] = TenantAdminCreationForm
        else:
            kwargs['form'] = TenantUpdateForm
        return super().get_form(request, obj, **kwargs)
    
    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return (
                ('Información del Tenant', {
                    'fields': ('name', 'email', 'phone', 'notes')
                }),
                ('Configuración Técnica', {
                    'fields': ('schema_name', 'domain_name'),
                    'description': 'Configuración técnica del tenant'
                }),
                ('Usuario Principal', {
                    'fields': ('username', 'password'),
                    'description': 'Credenciales del usuario principal del tenant'
                }),
            )
        else:
            return (
                ('Información del Nutricionista', {
                    'fields': ('name', 'email', 'phone', 'professional_number')
                }),
                ('Configuración', {
                    'fields': ('schema_name',)
                }),
                ('Estado y Control', {
                    'fields': ('status', 'is_active', 'notes')
                }),
                ('Información del Sistema', {
                    'fields': ('created', 'modified', 'is_deleted', 'deleted_at', 'tenant_stats'),
                    'classes': ('collapse',)
                }),
            )
    
    def get_queryset(self, request):
        return Tenant.all_objects.all()
    
    def user_info(self, obj):
        """Muestra información del usuario asociado"""
        try:
            user = User.objects.filter(tenant=obj).first()
            if user:
                return format_html(
                    '<strong>{}</strong><br><small>{}</small>',
                    user.username,
                    user.get_full_name() or 'Sin nombre'
                )
            else:
                return format_html(
                    '<span style="color: red;">Sin usuario</span>'
                )
        except:
            return 'Error'
    user_info.short_description = 'Usuario'
    
    def domain_info(self, obj):
        """Muestra información del dominio principal"""
        try:
            domain = Domain.objects.filter(tenant=obj, is_primary=True).first()
            if domain:
                return format_html(
                    '<a href="http://{}" target="_blank">{}</a>',
                    domain.domain,
                    domain.domain
                )
            else:
                return format_html(
                    '<span style="color: orange;">Sin dominio</span>'
                )
        except:
            return 'Error'
    domain_info.short_description = 'Dominio'
    
    actions = ['activate_tenants', 'suspend_tenants', 'restore_tenants']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Solo para creación
            # El formulario ya maneja la creación completa
            tenant = form.save()
            # Asignar el tenant creado al obj para que el admin sepa que se creó
            for field in tenant._meta.fields:
                setattr(obj, field.name, getattr(tenant, field.name))
        else:
            super().save_model(request, obj, form, change)
    
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
