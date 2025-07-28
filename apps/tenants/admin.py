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
from .forms import TenantUpdateForm, TenantStatusForm
from .services import TenantService


class TenantCreationForm(forms.ModelForm):
    """Formulario para crear un tenant con su usuario asociado"""
    
    # Campos adicionales para el usuario
    username = forms.CharField(
        max_length=150,
        help_text="Nombre de usuario para acceder al sistema"
    )
    user_email = forms.EmailField(
        label="Email del usuario",
        help_text="Email para el usuario (puede ser diferente al del tenant)"
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Contraseña inicial para el usuario"
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        help_text="Nombre del usuario"
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        help_text="Apellidos del usuario"
    )
    create_domain = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Crear dominio automáticamente"
    )
    domain_name = forms.CharField(
        max_length=253,
        required=False,
        help_text="Nombre del dominio (ej: carlos.zentoerp.com). Si se deja vacío, se generará automáticamente."
    )
    
    class Meta:
        model = Tenant
        fields = ['name', 'email', 'phone', 'professional_number', 'notes']
    
    def save(self, commit=True):
        tenant = super().save(commit=False)
        
        if commit:
            # Generar schema_name automáticamente
            import re
            from django.conf import settings
            
            schema_base = re.sub(r'[^a-zA-Z0-9]', '', self.cleaned_data['username'].lower())
            tenant.schema_name = f"tenant_{schema_base}"
            
            # Asegurar que el schema_name sea único
            counter = 1
            original_schema = tenant.schema_name
            while Tenant.objects.filter(schema_name=tenant.schema_name).exists():
                tenant.schema_name = f"{original_schema}_{counter}"
                counter += 1
            
            tenant.save()
            
            # Crear usuario asociado
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['user_email'],
                password=self.cleaned_data['password'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                tenant=tenant
            )
            
            # Crear dominio si se solicita
            if self.cleaned_data.get('create_domain', True):
                # Usar dominio personalizado o generar uno automáticamente
                custom_domain = self.cleaned_data.get('domain_name', '').strip()
                
                if custom_domain:
                    domain_name = custom_domain
                else:
                    # Generar dominio automáticamente según el entorno
                    is_development = settings.DEBUG
                    
                    if is_development:
                        domain_name = f"{tenant.schema_name}.localhost"
                    else:
                        # En producción, usar zentoerp.com
                        domain_name = f"{tenant.schema_name}.zentoerp.com"
                
                Domain.objects.get_or_create(
                    domain=domain_name,
                    tenant=tenant,
                    defaults={'is_primary': True}
                )
        
        return tenant


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
    
    readonly_fields = [
        'created',
        'modified',
        'deleted_at',
        'schema_name',
        'tenant_stats'
    ]
    
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
        """Usar formulario especial para creación"""
        if obj is None:  # Creando nuevo tenant
            kwargs['form'] = TenantCreationForm
        else:  # Editando tenant existente
            kwargs['form'] = TenantUpdateForm
        return super().get_form(request, obj, **kwargs)
    
    def get_fieldsets(self, request, obj=None):
        """Usar fieldsets diferentes para creación y edición"""
        if obj is None:  # Creando nuevo tenant
            return (
                ('Información del Nutricionista', {
                    'fields': ('name', 'email', 'phone', 'professional_number', 'notes')
                }),
                ('Configuración de Usuario', {
                    'fields': ('username', 'user_email', 'password', 'first_name', 'last_name'),
                    'description': 'Datos para el usuario principal del tenant'
                }),
                ('Configuración de Dominio', {
                    'fields': ('create_domain', 'domain_name'),
                    'description': 'Configuración del dominio web'
                }),
                ('Estado', {
                    'fields': ('status',)
                }),
            )
        else:  # Editando tenant existente
            return super().get_fieldsets(request, obj)
    
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
