from django import forms
from django.core.exceptions import ValidationError
from apps.core.mixins import TenantFormMixin
from apps.core.constants import TENANT_ERROR_MESSAGES
from .models import Tenant
from .services import TenantValidationService
from .forms import TenantUpdateForm


class BaseTenantForm(forms.ModelForm, TenantFormMixin):
    schema_name = forms.CharField(
        max_length=50,
        label="Nombre del esquema",
        help_text="Identificador único para el tenant (solo letras, números y guiones bajos)"
    )
    
    class Meta:
        model = Tenant
        fields = ['name', 'email', 'phone', 'professional_number', 'schema_name']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_field_styling()
        self._setup_field_labels()
    
    def _setup_field_styling(self):
        field_configs = {
            'name': {'placeholder': 'Ej: María García Martínez'},
            'email': {'type': 'email', 'placeholder': 'maria@email.com'},
            'schema_name': {'placeholder': 'maria_garcia'},
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
            'schema_name': "Nombre del esquema",
            'phone': "Teléfono",
            'professional_number': "Número de colegiado"
        }
        
        help_texts = {
            'schema_name': "Solo letras, números y guiones bajos. Mínimo 3 caracteres.",
            'professional_number': "Opcional. Número de colegiado profesional"
        }
        
        for field_name, label in labels.items():
            if field_name in self.fields:
                self.fields[field_name].label = label
        
        for field_name, help_text in help_texts.items():
            if field_name in self.fields:
                self.fields[field_name].help_text = help_text
    
    def clean_schema_name(self):
        schema_name = self.cleaned_data['schema_name']
        is_valid, error_message = TenantValidationService.validate_schema_name_format(schema_name)
        if not is_valid:
            raise ValidationError(error_message)
        if not TenantValidationService.check_schema_name_availability(schema_name):
            raise ValidationError(f"El nombre de esquema '{schema_name}' ya está en uso.")
        return schema_name
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if not TenantValidationService.check_email_availability(email):
            raise ValidationError(
                TENANT_ERROR_MESSAGES['EMAIL_EXISTS'].format(email=email)
            )
        return email


class TenantRegistrationForm(BaseTenantForm):
    class Meta(BaseTenantForm.Meta):
        fields = ['name', 'email', 'schema_name']


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
