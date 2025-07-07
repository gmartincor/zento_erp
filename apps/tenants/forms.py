from django import forms
from django.core.exceptions import ValidationError
from apps.core.mixins import TenantFormMixin
from apps.core.constants import TENANT_DEFAULTS, TENANT_ERROR_MESSAGES
from .models import Tenant
from .services import TenantValidationService


class BaseTenantForm(forms.ModelForm, TenantFormMixin):
    class Meta:
        model = Tenant
        fields = ['name', 'email', 'slug', 'phone', 'professional_number']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_field_styling()
        self._setup_field_labels()
    
    def _setup_field_styling(self):
        field_configs = {
            'name': {'placeholder': 'Ej: María García Martínez'},
            'email': {'type': 'email', 'placeholder': 'maria@email.com'},
            'slug': {'placeholder': 'maria (se convertirá en /maria/)'},
            'phone': {'placeholder': '+34 600 123 456'},
            'professional_number': {'placeholder': 'Número de colegiado'}
        }
        
        for field_name, config in field_configs.items():
            if field_name in self.fields:
                self.apply_form_styling(self.fields[field_name], config)
    
    def _setup_field_labels(self):
        labels = {
            'name': "Nombre completo",
            'email': "Email",
            'slug': "Slug",
            'phone': "Teléfono",
            'professional_number': "Número de colegiado"
        }
        
        help_texts = {
            'slug': f"Solo letras, números y guiones. Mínimo {TENANT_DEFAULTS['MIN_SUBDOMAIN_LENGTH']} caracteres.",
            'professional_number': "Opcional. Número de colegiado profesional"
        }
        
        for field_name, label in labels.items():
            if field_name in self.fields:
                self.fields[field_name].label = label
        
        for field_name, help_text in help_texts.items():
            if field_name in self.fields:
                self.fields[field_name].help_text = help_text
    
    def clean_slug(self):
        slug = self.cleaned_data['slug']
        is_valid, error_message = TenantValidationService.validate_subdomain_format(slug)
        if not is_valid:
            raise ValidationError(error_message)
        if not TenantValidationService.check_subdomain_availability(slug):
            raise ValidationError(
                TENANT_ERROR_MESSAGES['SUBDOMAIN_EXISTS'].format(subdomain=slug)
            )
        return slug
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if not TenantValidationService.check_email_availability(email):
            raise ValidationError(
                TENANT_ERROR_MESSAGES['EMAIL_EXISTS'].format(email=email)
            )
        return email


class TenantRegistrationForm(BaseTenantForm):
    class Meta(BaseTenantForm.Meta):
        fields = ['name', 'email', 'slug']


class TenantUpdateForm(BaseTenantForm):
    class Meta(BaseTenantForm.Meta):
        fields = ['name', 'email', 'phone', 'professional_number', 'notes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'slug' in self.fields:
            del self.fields['slug']
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if self.instance and self.instance.email == email:
            return email
        return super().clean_email()


class TenantStatusForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['status', 'notes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].widget = forms.Select(
            attrs={'class': 'form-control'}
        )
        self.fields['notes'].widget = forms.Textarea(
            attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Razón del cambio de estado...'}
        )
        self.fields['status'].label = "Estado"
        self.fields['notes'].label = "Notas"
