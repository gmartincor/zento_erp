from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from apps.tenants.models import Tenant, Domain
from apps.tenants.services import TenantCreationService
from apps.authentication.models import User
import re


class TenantAdminCreationForm(forms.ModelForm):
    schema_name = forms.CharField(
        max_length=63,
        label="Schema name",
        help_text="Solo letras minúsculas, números y guiones bajos. Debe empezar con letra.",
        widget=forms.TextInput(attrs={'placeholder': 'ej: prueba9'})
    )
    
    domain_name = forms.CharField(
        max_length=253,
        label="Dominio",
        help_text="Dominio completo (ej: carlos.zentoerp.com para producción, carlos.localhost para desarrollo)",
        widget=forms.TextInput(attrs={
            'placeholder': 'ej: prueba9.zentoerp.com' if not settings.DEBUG else 'ej: prueba9.localhost'
        })
    )
    
    username = forms.CharField(
        max_length=150,
        label="Username",
        help_text="Nombre de usuario para acceder al sistema",
        widget=forms.TextInput(attrs={'placeholder': 'ej: prueba9'})
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña segura'}),
        label="Password",
        help_text="Contraseña para el usuario"
    )
    
    class Meta:
        model = Tenant
        fields = ['name', 'email', 'phone', 'notes']
        labels = {
            'name': 'Nombre del tenant',
            'email': 'Email del tenant',
            'phone': 'Teléfono',
            'notes': 'Notas adicionales'
        }
    
    class Media:
        js = ('admin/js/tenant_admin_form.js',)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['email'].required = True
        self.fields['schema_name'].required = True
        self.fields['domain_name'].required = True
        self.fields['username'].required = True
        self.fields['password'].required = True
        self.fields['phone'].required = False
        self.fields['notes'].required = False
        
        # Determinar el sufijo del dominio basado en el entorno
        domain_suffix = '.zentoerp.com' if not settings.DEBUG else '.localhost'
        
        # Auto-completar schema_name y domain_name basado en username
        if self.data and 'username' in self.data:
            username = self.data['username']
            if username and not self.data.get('schema_name'):
                clean_username = re.sub(r'[^a-z0-9_]', '', username.lower())
                self.fields['schema_name'].widget.attrs['value'] = clean_username
            if username and not self.data.get('domain_name'):
                clean_username = re.sub(r'[^a-z0-9_]', '', username.lower())
                self.fields['domain_name'].widget.attrs['value'] = f"{clean_username}{domain_suffix}"
    
    def clean_schema_name(self):
        schema_name = self.cleaned_data['schema_name']
        return TenantCreationService.validate_schema_name(schema_name)
    
    def clean_domain_name(self):
        domain_name = self.cleaned_data['domain_name']
        return TenantCreationService.validate_domain_name(domain_name)
    
    def clean_email(self):
        email = self.cleaned_data['email']
        return TenantCreationService.validate_email(email)
    
    def clean_username(self):
        username = self.cleaned_data['username']
        return TenantCreationService.validate_username(username)
    
    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)
        return self._create_complete_tenant()
    
    def _create_complete_tenant(self):
        tenant, domain, user = TenantCreationService.create_complete_tenant(
            schema_name=self.cleaned_data['schema_name'],
            tenant_name=self.cleaned_data['name'],
            email=self.cleaned_data['email'],
            phone=self.cleaned_data.get('phone', ''),
            notes=self.cleaned_data.get('notes', ''),
            domain_name=self.cleaned_data['domain_name'],
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        return tenant


class TenantUpdateForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['name', 'email', 'phone', 'professional_number', 'notes', 'status', 'is_active']
        labels = {
            'name': 'Nombre del tenant',
            'email': 'Email del tenant',
            'phone': 'Teléfono',
            'professional_number': 'Número profesional',
            'notes': 'Notas adicionales',
            'status': 'Estado',
            'is_active': 'Activo'
        }
    
    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        
        if self.instance and self.instance.email == email:
            return email
        
        if Tenant.objects.filter(email=email).exists():
            raise ValidationError(f'El email "{email}" ya está en uso')
        
        return email
