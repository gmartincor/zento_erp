from typing import Dict, Any
from django import forms
from django.core.exceptions import ValidationError

from apps.accounting.models import Client
from apps.accounting.services.validation_service import ValidationService


class ClientBaseForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['full_name', 'dni', 'gender', 'email', 'phone', 'notes', 'is_active']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'gender': forms.Select(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_field_styles()
        self._setup_required_fields()
    
    def _setup_field_styles(self):
        for field_name, field in self.fields.items():
            base_class = 'form-control bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5'
            
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': base_class,
                    'placeholder': f'Introduce {field.label.lower()}...'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': base_class.replace('p-2.5', 'p-2')
                })
            else:
                field.widget.attrs.update({
                    'class': base_class,
                    'placeholder': f'Introduce {field.label.lower()}...'
                })
            
            if field.required:
                field.widget.attrs['class'] += ' border-red-500'
                field.label = f"{field.label} *"
    
    def _setup_required_fields(self):
        self.fields['full_name'].required = True
        self.fields['dni'].required = True
        self.fields['gender'].required = True
    
    def clean_dni(self):
        dni = self.cleaned_data.get('dni', '').strip().upper()
        
        if not dni:
            raise forms.ValidationError("El DNI es obligatorio")
        
        try:
            ValidationService._is_valid_dni_format(dni)
        except:
            if not dni or len(dni) != 9:
                raise forms.ValidationError("El DNI debe tener 9 caracteres")
        
        queryset = Client.objects.filter(dni=dni)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError("Ya existe un cliente con este DNI")
        
        return dni
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        
        if email:
            try:
                if not ValidationService._is_valid_email_format(email):
                    raise forms.ValidationError("Formato de email inválido")
            except:
                if '@' not in email or '.' not in email:
                    raise forms.ValidationError("Formato de email inválido")
        
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        
        try:
            ValidationService.validate_client_data(cleaned_data)
        except ValidationError as e:
            raise forms.ValidationError(str(e))
        
        return cleaned_data


class ClientCreateForm(ClientBaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].initial = True
        self.fields['is_active'].widget = forms.HiddenInput()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.full_name = instance.full_name.strip().title()
        instance.dni = instance.dni.strip().upper()
        if instance.email:
            instance.email = instance.email.strip().lower()
        if commit:
            instance.save()
        return instance


class ClientUpdateForm(ClientBaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].widget = forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.full_name = instance.full_name.strip().title()
        instance.dni = instance.dni.strip().upper()
        if instance.email:
            instance.email = instance.email.strip().lower()
        if commit:
            instance.save()
        return instance


class ClientForm(ClientBaseForm):
    def __new__(cls, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance and instance.pk:
            return ClientUpdateForm(*args, **kwargs)
        else:
            return ClientCreateForm(*args, **kwargs)


class ClientQuickSearchForm(forms.Form):
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, DNI o email...',
            'autocomplete': 'off'
        })
    )
    
    def search_clients(self, queryset=None):
        if queryset is None:
            queryset = Client.objects.filter(is_active=True)
        
        search_term = self.cleaned_data.get('search', '').strip()
        
        if search_term:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(full_name__icontains=search_term) |
                Q(dni__icontains=search_term) |
                Q(email__icontains=search_term)
            )
        
        return queryset.order_by('full_name')


class ClientFilterForm(forms.Form):
    gender = forms.ChoiceField(
        choices=[('', 'Todos los géneros')] + Client.GenderChoices.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_active = forms.ChoiceField(
        choices=[('', 'Todos'), ('true', 'Activos'), ('false', 'Inactivos')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, DNI o email...'
        })
    )
    
    def filter_queryset(self, queryset):
        gender = self.cleaned_data.get('gender')
        is_active = self.cleaned_data.get('is_active')
        search = self.cleaned_data.get('search')
        
        if gender:
            queryset = queryset.filter(gender=gender)
        
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(dni__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset.order_by('full_name')


class ClientServiceAssignmentForm(forms.Form):
    business_line = forms.ModelChoiceField(
        queryset=None,
        empty_label="Selecciona una línea de negocio",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    category = forms.ChoiceField(
        choices=[('WHITE', 'Blanco'), ('BLACK', 'Negro')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            from apps.accounting.services.business_line_service import BusinessLineService
            service = BusinessLineService()
            accessible_lines = service.get_accessible_lines(user)
            self.fields['business_line'].queryset = accessible_lines
        else:
            from apps.business_lines.models import BusinessLine
            self.fields['business_line'].queryset = BusinessLine.objects.filter(is_active=True)
