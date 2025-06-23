from django import forms
from django.core.exceptions import ValidationError

from apps.accounting.models import Client, ClientService
from apps.business_lines.models import BusinessLine
from apps.accounting.services.business_line_service import BusinessLineService
from apps.accounting.services.client_service import ClientServiceOperations
from apps.accounting.services.validation_service import ValidationService
from apps.accounting.services.form_service import (
    FormInitializationService, 
    FormFieldService, 
    FormValidationService,
    ClientServiceFormHandler,
    ClientDataUpdater
)


class ServiceFormValidator:
    @staticmethod
    def validate_form_data(form_instance, cleaned_data):
        client = getattr(form_instance, '_get_temp_client_for_validation', lambda: cleaned_data.get('client'))()
        business_line = cleaned_data.get('business_line')
        category = cleaned_data.get('category')
        remanentes = cleaned_data.get('remanentes')
        
        if not business_line:
            form_instance.add_error('business_line', 'Este campo es requerido.')
        
        if not category:
            form_instance.add_error('category', 'Este campo es requerido.')
        
        if business_line and category:
            try:
                form_instance._validate_business_rules(
                    client, business_line, category, remanentes
                )
            except ValidationError as e:
                if hasattr(e, 'error_dict'):
                    for field, errors in e.error_dict.items():
                        form_instance.add_error(field, errors)
                else:
                    form_instance.add_error(None, str(e))

class BaseClientServiceForm(forms.ModelForm):
    class Meta:
        model = ClientService
        fields = [
            'client', 'business_line', 'category', 'remanentes'
        ]
        widgets = {
            'remanentes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
            }),
            'client': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
            }),
            'business_line': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.business_line = kwargs.pop('business_line', None)
        self.category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)
        self._setup_form_fields()
        self._configure_form_display()
    
    def _setup_form_fields(self):
        if self.user:
            business_line_service = BusinessLineService()
            accessible_lines = business_line_service.get_accessible_lines(self.user)
            self.fields['business_line'].queryset = accessible_lines
        
        if self.business_line:
            self.fields['business_line'].initial = self.business_line
            self.fields['business_line'].widget = forms.HiddenInput()
            
        if self.category:
            self.fields['category'].initial = self.category
            self.fields['category'].widget = forms.HiddenInput()
    
    def _configure_form_display(self):
        FormInitializationService.apply_consistent_styling(self)
        FormInitializationService.configure_date_widgets(self)
        self._enhance_field_metadata()
    
    def _enhance_field_metadata(self):
        field_enhancements = {
            'client': {
                'help_text': 'Selecciona el cliente para este servicio'
            },
            'business_line': {
                'help_text': 'Línea de negocio a la que pertenece el servicio'
            },
            'category': {
                'help_text': 'Categoría del servicio (WHITE o BLACK)'
            },
            'remanentes': {
                'help_text': 'Solo para categoría BLACK. Formato JSON válido.'
            }
        }
        for field_name, enhancements in field_enhancements.items():
            if field_name in self.fields:
                for attr, value in enhancements.items():
                    setattr(self.fields[field_name], attr, value)
    
    def clean(self):
        cleaned_data = super().clean()
        ServiceFormValidator.validate_form_data(self, cleaned_data)
        return cleaned_data
    
    def _validate_business_rules(self, client, business_line, category, remanentes):
        pass


class ClientServiceCreateForm(BaseClientServiceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_client_creation_fields()
        self.fields.pop('client', None)
    
    def _add_client_creation_fields(self):
        client_fields = FormFieldService.create_client_fields()
        new_fields = {}
        for field_name, field in client_fields.items():
            new_fields[field_name] = field
        for field_name, field in self.fields.items():
            new_fields[field_name] = field
        self.fields = new_fields
    
    def clean_client_dni(self):
        dni = self.cleaned_data.get('client_dni')
        if dni and Client.objects.filter(dni=dni, is_deleted=False).exists():
            raise forms.ValidationError(f'Ya existe un cliente con DNI {dni}')
        return dni
    
    def _get_temp_client_for_validation(self):
        return Client(
            full_name=self.cleaned_data.get('client_name', ''),
            dni=self.cleaned_data.get('client_dni', ''),
            gender=self.cleaned_data.get('client_gender', '')
        )
    
    def _validate_business_rules(self, client, business_line, category, remanentes):
        if category == 'BLACK' and business_line.has_remanente:
            if not business_line.remanente_field:
                raise ValidationError('La línea de negocio no tiene configurado el tipo de remanente.')
        
        if hasattr(client, 'pk') and client.pk:
            existing = ClientService.objects.filter(
                client=client,
                business_line=business_line,
                category=category,
                is_active=True
            ).exists()
            if existing:
                raise ValidationError(
                    f'El cliente ya tiene un servicio {category} activo en {business_line.name}'
                )
    
    def save(self, commit=True):
        if commit:
            client = self._create_client()
            
            client_service_ops = ClientServiceOperations()
            return client_service_ops.create_client_service(
                client=client,
                business_line=self.cleaned_data['business_line'],
                category=self.cleaned_data['category'],
                remanentes=self.cleaned_data.get('remanentes')
            )
        return self.instance
    
    def _create_client(self):
        client_service_ops = ClientServiceOperations()
        return client_service_ops.create_client(
            full_name=self.cleaned_data['client_name'],
            dni=self.cleaned_data['client_dni'],
            gender=self.cleaned_data['client_gender'],
            email=self.cleaned_data.get('client_email', ''),
            phone=self.cleaned_data.get('client_phone', ''),
            notes=self.cleaned_data.get('client_notes', '')
        )


class ClientServiceUpdateForm(BaseClientServiceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hide_client_field()
        self._add_client_edit_fields()
        self._setup_hidden_fields()
    
    def _setup_hidden_fields(self):
        if self.instance and self.instance.pk:
            if 'business_line' in self.fields:
                self.fields['business_line'].initial = self.instance.business_line
                self.fields['business_line'].widget = forms.HiddenInput()
            
            if 'category' in self.fields:
                self.fields['category'].initial = self.instance.category
                self.fields['category'].widget = forms.HiddenInput()
    
    def _hide_client_field(self):
        if 'client' in self.fields:
            self.fields['client'].widget = forms.HiddenInput()
            if self.instance and self.instance.client:
                self.fields['client'].initial = self.instance.client
    
    def _add_client_edit_fields(self):
        if self.instance and self.instance.client:
            ClientServiceFormHandler.setup_update_form(self, self.instance.client)
    
    def clean_client_dni(self):
        dni = self.cleaned_data.get('client_dni')
        if dni and self.instance and self.instance.client:
            existing_client = Client.objects.filter(
                dni=dni, is_deleted=False
            ).exclude(id=self.instance.client.id).first()
            if existing_client:
                raise forms.ValidationError(f'Ya existe un cliente con DNI {dni}')
        return dni
    
    def _validate_business_rules(self, client, business_line, category, remanentes):
        if category == 'BLACK' and business_line.has_remanente:
            if not business_line.remanente_field:
                raise ValidationError('La línea de negocio no tiene configurado el tipo de remanente.')
    
    def save(self, commit=True):
        if commit:
            if self.instance and self.instance.client:
                ClientDataUpdater.update_client_from_form_data(
                    self.instance.client, 
                    self.cleaned_data
                )
            
            service = self.instance
            service.remanentes = self.cleaned_data.get('remanentes', {})
            
            service.save()
            return service
        return super().save(commit=False)


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
