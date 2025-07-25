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
    
    period_start = forms.DateField(
        label="Fecha de inicio del primer período",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Fecha de inicio del primer período de facturación"
    )
    
    period_end = forms.DateField(
        label="Fecha de fin del primer período", 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Fecha de fin del primer período de facturación"
    )
    
    class Meta:
        model = ClientService
        fields = [
            'business_line', 'category', 
            'price', 'start_date', 'admin_status', 'is_active', 'notes', 'remanentes'
        ]
        widgets = {
            'price': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.business_line = kwargs.pop('business_line', None)
        self.category = kwargs.pop('category', None)
        self.source_service = kwargs.pop('source_service', None)
        super().__init__(*args, **kwargs)
        self.setup_form_styles()
        self.setup_business_line_context(self.user, self.business_line, self.category)
        
        from apps.core.form_utils import apply_currency_field_styles
        apply_currency_field_styles(self.fields['price'])
        
        if self.source_service:
            self.setup_source_service_data()
        self._setup_period_fields()
    
    def _setup_period_fields(self):
        """Configura los campos de período según el tipo de formulario"""
        # Solo mostrar campos de período en formularios de creación
        if self.instance and self.instance.pk:
            # Es un formulario de edición, ocultar campos de período
            if 'period_start' in self.fields:
                del self.fields['period_start']
            if 'period_end' in self.fields:
                del self.fields['period_end']
        else:
            # Es un formulario de creación, ocultar start_date y mostrar campos de período
            if 'start_date' in self.fields:
                del self.fields['start_date']
            
            from django.utils import timezone
            today = timezone.now().date()
            if 'period_start' in self.fields:
                self.fields['period_start'].initial = today
                # Configurar clases CSS
                self.fields['period_start'].widget.attrs.update({
                    'class': 'form-control',
                    'type': 'date'
                })
            if 'period_end' in self.fields:
                self.fields['period_end'].widget.attrs.update({
                    'class': 'form-control', 
                    'type': 'date'
                })
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar campos de período si existen
        period_start = cleaned_data.get('period_start')
        period_end = cleaned_data.get('period_end')
        
        # Solo validar si estamos en un formulario de creación (los campos existen)
        if 'period_start' in self.fields or 'period_end' in self.fields:
            if not period_start:
                raise forms.ValidationError({
                    'period_start': 'Este campo es obligatorio.'
                })
            if not period_end:
                raise forms.ValidationError({
                    'period_end': 'Este campo es obligatorio.'
                })
            
            if period_start and period_end:
                if period_start >= period_end:
                    raise forms.ValidationError({
                        'period_end': 'La fecha de fin del período debe ser posterior a la fecha de inicio.'
                    })
                
                # Establecer start_date del servicio igual al period_start
                cleaned_data['start_date'] = period_start
        
        return cleaned_data


class ClientServiceCreateForm(BaseClientServiceForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_client_fields()

    def clean(self):
        cleaned_data = super().clean()
        # Normalize DNI for consistent lookup
        dni = cleaned_data.get('client_dni', '').strip().upper()
        if dni:
            # Check for existing client (not deleted)
            existing_client = Client.objects.filter(dni=dni, is_deleted=False).first()
            if existing_client:
                # Reuse existing client, update fields if needed
                cleaned_data['client_instance'] = existing_client
            # If not found, will be created in transaction manager
        self.validate_client_data(cleaned_data)
        self.validate_service_data(cleaned_data)
        self.validate_service_business_rules(cleaned_data)
        return cleaned_data

    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)

        from apps.accounting.services.client_service_transaction import ClientServiceTransactionManager

        # Pass client_instance if found, else rely on transaction manager to create
        form_data = self.cleaned_data.copy()
        if 'client_instance' in form_data:
            form_data['client_dni'] = form_data['client_instance'].dni
        return ClientServiceTransactionManager.create_client_service(
            form_data,
            self.business_line,
            self.category
        )


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
        
        from apps.accounting.services.client_service_transaction import ClientServiceTransactionManager
        
        form_data = self.cleaned_data.copy()
        
        for field_name, field_value in self.cleaned_data.items():
            if field_name.startswith('client_'):
                form_data[field_name] = field_value
            elif field_name in ['price', 'start_date', 'end_date', 'admin_status', 'is_active', 'notes', 'remanentes']:
                form_data[field_name] = field_value
        
        return ClientServiceTransactionManager.update_client_service(self.instance, form_data)


class ServiceRenewalForm(BaseClientServiceForm):
    
    def __init__(self, *args, **kwargs):
        self.original_service = kwargs.pop('original_service', None)
        super().__init__(*args, **kwargs)
        if self.original_service:
            self._prefill_from_original()
    
    def _prefill_from_original(self):
        if self.original_service:
            self.fields['price'].initial = self.original_service.price
            self.fields['business_line'].initial = self.original_service.business_line
            self.fields['category'].initial = self.original_service.category
            
    def clean(self):
        cleaned_data = super().clean()
        self.validate_service_data(cleaned_data)
        return cleaned_data
    
    def save(self, commit=True):
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
