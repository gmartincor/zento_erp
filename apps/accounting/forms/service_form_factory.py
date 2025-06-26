from typing import Dict, Any, Optional
from django import forms

from apps.accounting.models import ClientService, Client
from apps.accounting.forms.form_mixins import ServiceFormMixin, ClientFieldsMixin, ServiceFieldsMixin
from apps.accounting.forms.service_date_form import ServiceDateEditForm


class ServiceFormFactory:
    
    @staticmethod
    def create_service_form(form_type: str, **kwargs):
        forms_map = {
            'create': ClientServiceCreateForm,
            'update': ClientServiceUpdateForm,
            'renewal': ServiceRenewalForm
        }
        
        form_class = forms_map.get(form_type)
        if not form_class:
            raise ValueError(f"Unknown form type: {form_type}")
            
        return form_class(**kwargs)
    
    @staticmethod
    def get_create_form(category=None):
        return ClientServiceCreateForm
    
    @staticmethod
    def get_update_form(category=None):
        return ClientServiceUpdateForm
    
    @staticmethod
    def get_renewal_form(category=None):
        return ServiceRenewalForm
    
    @staticmethod
    def get_filter_form(category=None):
        return ClientServiceFilterForm


class BaseClientServiceForm(ServiceFormMixin, ClientFieldsMixin, ServiceFieldsMixin, ServiceDateEditForm, forms.ModelForm):
    class Meta:
        model = ClientService
        fields = [
            'client', 'business_line', 'category', 
            'price', 'start_date', 'end_date', 'status', 'notes', 'remanentes'
        ]
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.business_line = kwargs.pop('business_line', None)
        self.category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)
        self.setup_form_styles()
        self.setup_business_line_context(self.user, self.business_line, self.category)


class ClientServiceCreateForm(BaseClientServiceForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_client_fields()
    
    def clean(self):
        cleaned_data = super().clean()
        self.validate_client_data(cleaned_data)
        self.validate_service_data(cleaned_data)
        self.validate_service_business_rules(cleaned_data)
        return cleaned_data
    
    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)
        
        return super().save(commit=True)


class ClientServiceUpdateForm(BaseClientServiceForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.add_client_fields(self.instance.client)
            self._setup_hidden_fields()
    
    def _setup_hidden_fields(self):
        if self.instance and self.instance.pk:
            for field_name in ['business_line', 'category', 'client']:
                if field_name in self.fields:
                    self.fields[field_name].widget = forms.HiddenInput()
                    if hasattr(self.instance, field_name):
                        self.fields[field_name].initial = getattr(self.instance, field_name)
    
    def clean(self):
        cleaned_data = super().clean()
        self.validate_client_data(cleaned_data, self.instance.client if self.instance else None)
        self.validate_service_data(cleaned_data)
        self.validate_service_business_rules(cleaned_data, self.instance)
        return cleaned_data
    
    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)
        
        return super().save(commit=True)


class ServiceRenewalForm(BaseClientServiceForm):
    """
    Formulario simplificado para renovación de servicios.
    La lógica de renovación se maneja en service_manager.py
    """
    
    def __init__(self, *args, **kwargs):
        self.original_service = kwargs.pop('original_service', None)
        super().__init__(*args, **kwargs)
        if self.original_service:
            self._prefill_from_original()
    
    def _prefill_from_original(self):
        """Prefilla el formulario con datos del servicio original"""
        if self.original_service:
            self.fields['price'].initial = self.original_service.price
            self.fields['business_line'].initial = self.original_service.business_line
            self.fields['category'].initial = self.original_service.category
            
    def clean(self):
        cleaned_data = super().clean()
        self.validate_service_data(cleaned_data)
        return cleaned_data
    
    def save(self, commit=True):
        """
        Guarda el nuevo servicio usando el ServiceManager.
        La lógica de renovación está centralizada en service_manager.py
        """
        if not commit:
            return super().save(commit=False)
        
        # Solo crear el servicio, la lógica de renovación se maneja externamente
        return super().save(commit=True)


class ClientServiceFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por cliente, DNI o notas...',
            'class': 'form-control'
        })
    )
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas las categorías')] + ClientService.CategoryChoices.choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
