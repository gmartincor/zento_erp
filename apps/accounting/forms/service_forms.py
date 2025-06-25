from django import forms
from django.core.exceptions import ValidationError

from apps.accounting.models import Client, ClientService
from apps.accounting.forms.form_mixins import ServiceFormMixin, ClientFieldsMixin, ServiceFieldsMixin
from apps.accounting.services.service_workflow_manager import ServiceWorkflowManager


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
