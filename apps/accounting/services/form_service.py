from datetime import date
from typing import Dict, Any, Optional
from django import forms

class FormInitializationService:
    @staticmethod
    def format_date_for_html_input(date_value) -> Optional[str]:
        if not date_value:
            return None
        if isinstance(date_value, str):
            return date_value
        if hasattr(date_value, 'date'):
            return date_value.date().isoformat()
        if hasattr(date_value, 'isoformat'):
            return date_value.isoformat()
        return None
    
    @staticmethod
    def apply_consistent_styling(form_instance: forms.Form) -> None:
        base_input_classes = (
            'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 '
            'rounded-md shadow-sm focus:outline-none focus:ring-primary-500 '
            'focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        )
        widget_classes = {
            forms.TextInput: base_input_classes,
            forms.EmailInput: base_input_classes,
            forms.NumberInput: base_input_classes,
            forms.DateInput: base_input_classes,
            forms.Select: base_input_classes,
            forms.Textarea: base_input_classes,
            forms.CheckboxInput: 'mr-2',
            forms.HiddenInput: '',
        }
        for field_name, field in form_instance.fields.items():
            widget_type = type(field.widget)
            if widget_type in widget_classes:
                existing_classes = field.widget.attrs.get('class', '')
                new_classes = widget_classes[widget_type]
                if not existing_classes and new_classes:
                    field.widget.attrs['class'] = new_classes
    
    @staticmethod
    def configure_date_widgets(form_instance: forms.Form) -> None:
        date_fields = ['start_date', 'renewal_date', 'birth_date', 'date_from', 'date_to']
        for field_name in date_fields:
            if field_name in form_instance.fields:
                field = form_instance.fields[field_name]
                if isinstance(field.widget, forms.DateInput):
                    field.widget.attrs['type'] = 'date'
                    if 'class' not in field.widget.attrs:
                        field.widget.attrs['class'] = (
                            'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 '
                            'rounded-md shadow-sm focus:outline-none focus:ring-primary-500 '
                            'focus:border-primary-500 dark:bg-gray-700 dark:text-white'
                        )

class FormFieldService:
    @staticmethod
    def create_client_fields() -> Dict[str, forms.Field]:
        input_classes = (
            'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 '
            'rounded-md shadow-sm focus:outline-none focus:ring-primary-500 '
            'focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        )
        from apps.accounting.models import Client
        return {
            'client_name': forms.CharField(
                required=True,
                max_length=255,
                label='Nombre completo',
                help_text='Nombre completo del cliente',
                widget=forms.TextInput(attrs={'class': input_classes})
            ),
            'client_dni': forms.CharField(
                required=True,
                max_length=20,
                label='DNI/NIE',
                help_text='Documento de identidad del cliente',
                widget=forms.TextInput(attrs={'class': input_classes})
            ),
            'client_gender': forms.ChoiceField(
                required=True,
                choices=Client.GenderChoices.choices,
                label='Género',
                widget=forms.Select(attrs={'class': input_classes})
            ),
            'client_email': forms.EmailField(
                required=False,
                label='Email',
                widget=forms.EmailInput(attrs={'class': input_classes})
            ),
            'client_phone': forms.CharField(
                required=False,
                max_length=20,
                label='Teléfono',
                widget=forms.TextInput(attrs={'class': input_classes})
            ),
        }
    
    @staticmethod
    def populate_client_fields_with_data(fields: Dict[str, forms.Field], client) -> None:
        if not client:
            return
        field_mapping = {
            'client_name': 'full_name',
            'client_dni': 'dni', 
            'client_gender': 'gender',
            'client_email': 'email',
            'client_phone': 'phone'
        }
        for field_name, model_field in field_mapping.items():
            if field_name in fields and hasattr(client, model_field):
                fields[field_name].initial = getattr(client, model_field)

class FormValidationService:
    @staticmethod
    def validate_required_fields(cleaned_data: Dict[str, Any], required_fields: list) -> Dict[str, list]:
        errors = {}
        for field in required_fields:
            if not cleaned_data.get(field):
                errors[field] = ['Este campo es requerido.']
        return errors
    
    @staticmethod
    def validate_date_range(start_date, end_date) -> Optional[str]:
        if start_date and end_date and start_date > end_date:
            return 'La fecha de inicio no puede ser posterior a la fecha de fin.'
        return None
