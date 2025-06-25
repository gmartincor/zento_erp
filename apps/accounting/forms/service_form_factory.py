from typing import Dict, Any, Optional
from django import forms

from apps.accounting.models import ClientService, Client
from apps.accounting.forms.form_mixins import ServiceFormMixin, ClientFieldsMixin, ServiceFieldsMixin
from apps.accounting.services.service_workflow_manager import ServiceWorkflowManager
from apps.accounting.services.service_renewal_manager import ServiceRenewalManager


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


class BaseClientServiceForm(ServiceFormMixin, ClientFieldsMixin, ServiceFieldsMixin, forms.ModelForm):
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
        
        return ServiceWorkflowManager.handle_service_creation_flow(
            None, self.cleaned_data, 
            self.cleaned_data['business_line'], 
            self.cleaned_data['category']
        )[0]


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
        
        return ServiceWorkflowManager.handle_service_update_flow(
            None, self.instance, self.cleaned_data
        )[0]


class ServiceRenewalForm(BaseClientServiceForm):
    
    def __init__(self, *args, **kwargs):
        self.original_service = kwargs.pop('original_service', None)
        super().__init__(*args, **kwargs)
        if self.original_service:
            self._prefill_from_original()
    
    def _prefill_from_original(self):
        suggestions = ServiceRenewalManager.get_renewal_suggestions(self.original_service)
        self.fields['price'].initial = suggestions['suggested_price']
    
    def clean(self):
        cleaned_data = super().clean()
        self.validate_service_data(cleaned_data)
        return cleaned_data
    
    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)
        
        return ServiceRenewalManager.create_renewal_service(
            self.original_service, self.cleaned_data
        )[0]


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
