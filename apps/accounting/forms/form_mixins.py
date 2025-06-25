from typing import Dict, Any, Optional
from django import forms
from django.core.exceptions import ValidationError

from apps.accounting.models import Client, ClientService
from apps.accounting.services.service_workflow_manager import ServiceWorkflowManager


class ServiceFormMixin:
    
    def setup_form_styles(self, base_class: str = None):
        if not base_class:
            base_class = ('w-full px-3 py-2 border border-gray-300 dark:border-gray-600 '
                         'rounded-md shadow-sm focus:outline-none focus:ring-primary-500 '
                         'focus:border-primary-500 dark:bg-gray-700 dark:text-white')
        
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': base_class,
                    'rows': getattr(field.widget.attrs, 'rows', 3)
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': base_class})
            elif isinstance(field.widget, forms.NumberInput):
                field.widget.attrs.update({
                    'class': base_class,
                    'step': '0.01',
                    'min': '0'
                })
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({
                    'class': base_class,
                    'type': 'date'
                })
            else:
                field.widget.attrs.update({'class': base_class})
    
    def setup_business_line_context(self, user, business_line=None, category=None):
        if user:
            from apps.accounting.services.business_line_service import BusinessLineService
            business_line_service = BusinessLineService()
            accessible_lines = business_line_service.get_accessible_lines(user)
            
            if 'business_line' in self.fields:
                self.fields['business_line'].queryset = accessible_lines
                
                if business_line:
                    self.fields['business_line'].initial = business_line
                    self.fields['business_line'].widget = forms.HiddenInput()
        
        if category and 'category' in self.fields:
            self.fields['category'].initial = category
            self.fields['category'].widget = forms.HiddenInput()


class ClientFieldsMixin:
    
    def add_client_fields(self, client: Client = None):
        client_fields = self._get_client_field_definitions(client)
        
        new_fields = {}
        for field_name, field in client_fields.items():
            new_fields[field_name] = field
        
        for field_name, field in self.fields.items():
            if field_name != 'client':
                new_fields[field_name] = field
        
        self.fields = new_fields
        
        if 'client' in self.fields:
            self.fields.pop('client', None)
    
    def _get_client_field_definitions(self, client: Client = None):
        base_attrs = {
            'class': ('w-full px-3 py-2 border border-gray-300 dark:border-gray-600 '
                     'rounded-md shadow-sm focus:outline-none focus:ring-primary-500 '
                     'focus:border-primary-500 dark:bg-gray-700 dark:text-white')
        }
        
        return {
            'client_name': forms.CharField(
                required=True,
                max_length=255,
                label='Nombre completo',
                initial=client.full_name if client else '',
                widget=forms.TextInput(attrs=base_attrs)
            ),
            'client_dni': forms.CharField(
                required=True,
                max_length=20,
                label='DNI/NIE',
                initial=client.dni if client else '',
                widget=forms.TextInput(attrs=base_attrs)
            ),
            'client_gender': forms.ChoiceField(
                required=True,
                choices=Client.GenderChoices.choices,
                label='Género',
                initial=client.gender if client else '',
                widget=forms.Select(attrs=base_attrs)
            ),
            'client_email': forms.EmailField(
                required=False,
                label='Email',
                initial=client.email if client else '',
                widget=forms.EmailInput(attrs=base_attrs)
            ),
            'client_phone': forms.CharField(
                required=False,
                max_length=20,
                label='Teléfono',
                initial=client.phone if client else '',
                widget=forms.TextInput(attrs=base_attrs)
            ),
            'client_notes': forms.CharField(
                required=False,
                label='Notas',
                initial=client.notes if client else '',
                widget=forms.Textarea(attrs={**base_attrs, 'rows': 3})
            ),
        }
    
    def validate_client_data(self, cleaned_data: Dict[str, Any], existing_client: Client = None):
        client_name = cleaned_data.get('client_name', '').strip()
        client_dni = cleaned_data.get('client_dni', '').strip().upper()
        client_gender = cleaned_data.get('client_gender')
        client_email = cleaned_data.get('client_email', '').strip()
        
        errors = {}
        
        if not client_name or len(client_name) < 2:
            errors['client_name'] = 'El nombre debe tener al menos 2 caracteres'
        
        if not client_dni or len(client_dni) != 9:
            errors['client_dni'] = 'El DNI debe tener 9 caracteres'
        elif not client_dni[:-1].isdigit() or not client_dni[-1].isalpha():
            errors['client_dni'] = 'Formato de DNI inválido (8 dígitos + 1 letra)'
        
        if not client_gender:
            errors['client_gender'] = 'El género es obligatorio'
        
        if client_email and '@' not in client_email:
            errors['client_email'] = 'Formato de email inválido'
        
        if existing_client:
            if Client.objects.filter(dni=client_dni).exclude(pk=existing_client.pk).exists():
                errors['client_dni'] = f'Ya existe otro cliente con el DNI {client_dni}'
        else:
            if Client.objects.filter(dni=client_dni, is_deleted=False).exists():
                errors['client_dni'] = f'Ya existe un cliente con DNI {client_dni}'
        
        if errors:
            raise ValidationError(errors)
        
        return cleaned_data


class ServiceFieldsMixin:
    
    def validate_service_data(self, cleaned_data: Dict[str, Any]):
        price = cleaned_data.get('price')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        errors = {}
        
        if price is not None and price < 0:
            errors['price'] = 'El precio no puede ser negativo'
        
        if start_date and end_date and start_date > end_date:
            errors['end_date'] = 'La fecha de fin no puede ser anterior a la fecha de inicio'
        
        if errors:
            raise ValidationError(errors)
        
        return cleaned_data
    
    def validate_service_business_rules(self, cleaned_data: Dict[str, Any], existing_service: ClientService = None):
        business_line = cleaned_data.get('business_line')
        category = cleaned_data.get('category')
        
        if not business_line or not category:
            return cleaned_data
        
        if category == 'BLACK' and business_line.has_remanente and not business_line.remanente_field:
            raise ValidationError({
                'business_line': 'La línea de negocio no tiene configurado el tipo de remanente.'
            })
        
        return cleaned_data
