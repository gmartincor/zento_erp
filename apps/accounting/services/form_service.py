from typing import Dict, Any, Optional
from django import forms

class FormStyleConstants:
    BASE_INPUT_CLASSES = (
        'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 '
        'rounded-md shadow-sm focus:outline-none focus:ring-primary-500 '
        'focus:border-primary-500 dark:bg-gray-700 dark:text-white'
    )

class DateFieldHandler:
    @staticmethod
    def setup_date_field(field: forms.DateField) -> None:
        if isinstance(field.widget, forms.DateInput):
            field.widget.attrs.update({
                'type': 'date',
                'class': FormStyleConstants.BASE_INPUT_CLASSES
            })

class FormInitializationService:
    @staticmethod
    def apply_consistent_styling(form_instance: forms.Form) -> None:
        widget_classes = {
            forms.TextInput: FormStyleConstants.BASE_INPUT_CLASSES,
            forms.EmailInput: FormStyleConstants.BASE_INPUT_CLASSES,
            forms.NumberInput: FormStyleConstants.BASE_INPUT_CLASSES,
            forms.DateInput: FormStyleConstants.BASE_INPUT_CLASSES,
            forms.Select: FormStyleConstants.BASE_INPUT_CLASSES,
            forms.Textarea: FormStyleConstants.BASE_INPUT_CLASSES,
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
                DateFieldHandler.setup_date_field(form_instance.fields[field_name])

class FormFieldService:
    @staticmethod
    def create_client_fields() -> Dict[str, forms.Field]:
        from apps.accounting.models import Client
        return {
            'client_name': forms.CharField(
                required=True,
                max_length=255,
                label='Nombre completo',
                help_text='Nombre completo del cliente',
                widget=forms.TextInput(attrs={'class': FormStyleConstants.BASE_INPUT_CLASSES})
            ),
            'client_dni': forms.CharField(
                required=True,
                max_length=20,
                label='DNI/NIE',
                help_text='Documento de identidad del cliente',
                widget=forms.TextInput(attrs={'class': FormStyleConstants.BASE_INPUT_CLASSES})
            ),
            'client_gender': forms.ChoiceField(
                required=True,
                choices=Client.GenderChoices.choices,
                label='Género',
                widget=forms.Select(attrs={'class': FormStyleConstants.BASE_INPUT_CLASSES})
            ),
            'client_email': forms.EmailField(
                required=False,
                label='Email',
                widget=forms.EmailInput(attrs={'class': FormStyleConstants.BASE_INPUT_CLASSES})
            ),
            'client_phone': forms.CharField(
                required=False,
                max_length=20,
                label='Teléfono',
                widget=forms.TextInput(attrs={'class': FormStyleConstants.BASE_INPUT_CLASSES})
            ),
            'client_notes': forms.CharField(
                required=False,
                label='Notas',
                help_text='Información adicional sobre el cliente',
                widget=forms.Textarea(attrs={
                    'class': FormStyleConstants.BASE_INPUT_CLASSES,
                    'rows': 3,
                    'placeholder': 'Información adicional, observaciones médicas, etc.'
                })
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
            'client_phone': 'phone',
            'client_notes': 'notes'
        }
        for field_name, model_field in field_mapping.items():
            if field_name in fields and hasattr(client, model_field):
                fields[field_name].initial = getattr(client, model_field)

class ClientDataUpdater:
    @staticmethod
    def update_client_from_form_data(client, cleaned_data):
        field_mapping = {
            'client_name': 'full_name',
            'client_dni': 'dni', 
            'client_gender': 'gender',
            'client_email': 'email',
            'client_phone': 'phone',
            'client_notes': 'notes'
        }
        
        for form_field, model_field in field_mapping.items():
            if form_field in cleaned_data:
                setattr(client, model_field, cleaned_data.get(form_field, getattr(client, model_field)))
        
        client.save()

class ClientServiceFormHandler:
    @staticmethod
    def setup_update_form(form_instance, client_instance):
        if client_instance:
            client_fields = FormFieldService.create_client_fields()
            FormFieldService.populate_client_fields_with_data(client_fields, client_instance)
            
            for field_name, field in client_fields.items():
                form_instance.fields[field_name] = field

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
