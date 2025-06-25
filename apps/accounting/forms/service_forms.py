from django import forms
from django.core.exceptions import ValidationError

from apps.accounting.models import Client, ClientService
from apps.business_lines.models import BusinessLine
from apps.accounting.services.client_service_transaction import ClientServiceTransactionManager


class ClientServiceFormValidator:
    
    @staticmethod
    def validate_client_data(cleaned_data):
        client_name = cleaned_data.get('client_name', '').strip()
        client_dni = cleaned_data.get('client_dni', '').strip().upper()
        client_gender = cleaned_data.get('client_gender')
        client_email = cleaned_data.get('client_email', '').strip()
        
        errors = {}
        
        if not client_name:
            errors['client_name'] = 'El nombre es obligatorio'
        
        if not client_dni:
            errors['client_dni'] = 'El DNI es obligatorio'
        elif len(client_dni) != 9:
            errors['client_dni'] = 'El DNI debe tener 9 caracteres'
        
        if not client_gender:
            errors['client_gender'] = 'El género es obligatorio'
        
        if client_email and '@' not in client_email:
            errors['client_email'] = 'Formato de email inválido'
        
        if errors:
            raise ValidationError(errors)
        
        return cleaned_data
    
    @staticmethod
    def validate_service_rules(business_line, category, remanentes, client=None):
        if category == 'BLACK' and business_line.has_remanente:
            if not business_line.remanente_field:
                raise ValidationError('La línea de negocio no tiene configurado el tipo de remanente.')
        
        if client and hasattr(client, 'pk') and client.pk:
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


class BaseClientServiceForm(forms.ModelForm):
    class Meta:
        model = ClientService
        fields = [
            'client', 'business_line', 'category', 
            'price', 'start_date', 'end_date', 'status', 'notes', 'remanentes'
        ]
        widgets = {
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white',
                'step': '0.01',
                'min': '0'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
            }),
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
        self._setup_fields()
    
    def _setup_fields(self):
        if self.user:
            from apps.accounting.services.business_line_service import BusinessLineService
            business_line_service = BusinessLineService()
            accessible_lines = business_line_service.get_accessible_lines(self.user)
            self.fields['business_line'].queryset = accessible_lines
        
        if self.business_line:
            self.fields['business_line'].initial = self.business_line
            self.fields['business_line'].widget = forms.HiddenInput()
            
        if self.category:
            self.fields['category'].initial = self.category
            self.fields['category'].widget = forms.HiddenInput()


class ClientServiceCreateForm(BaseClientServiceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_client_fields()
        self.fields.pop('client', None)
    
    def _add_client_fields(self):
        client_fields = {
            'client_name': forms.CharField(
                required=True,
                max_length=255,
                label='Nombre completo',
                widget=forms.TextInput(attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
                })
            ),
            'client_dni': forms.CharField(
                required=True,
                max_length=20,
                label='DNI/NIE',
                widget=forms.TextInput(attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
                })
            ),
            'client_gender': forms.ChoiceField(
                required=True,
                choices=Client.GenderChoices.choices,
                label='Género',
                widget=forms.Select(attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
                })
            ),
            'client_email': forms.EmailField(
                required=False,
                label='Email',
                widget=forms.EmailInput(attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
                })
            ),
            'client_phone': forms.CharField(
                required=False,
                max_length=20,
                label='Teléfono',
                widget=forms.TextInput(attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
                })
            ),
            'client_notes': forms.CharField(
                required=False,
                label='Notas',
                widget=forms.Textarea(attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white',
                    'rows': 3
                })
            ),
        }
        
        new_fields = {}
        for field_name, field in client_fields.items():
            new_fields[field_name] = field
        for field_name, field in self.fields.items():
            new_fields[field_name] = field
        self.fields = new_fields
    
    def clean(self):
        cleaned_data = super().clean()
        
        ClientServiceFormValidator.validate_client_data(cleaned_data)
        
        dni = cleaned_data.get('client_dni', '').strip().upper()
        if dni and Client.objects.filter(dni=dni, is_deleted=False).exists():
            raise ValidationError({'client_dni': f'Ya existe un cliente con DNI {dni}'})
        
        business_line = cleaned_data.get('business_line')
        category = cleaned_data.get('category')
        remanentes = cleaned_data.get('remanentes', {})
        
        if business_line and category:
            ClientServiceFormValidator.validate_service_rules(business_line, category, remanentes)
        
        return cleaned_data
    
    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)
        
        return ClientServiceTransactionManager.create_client_service(
            self.cleaned_data,
            self.cleaned_data['business_line'],
            self.cleaned_data['category']
        )


class ClientServiceUpdateForm(BaseClientServiceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_client_fields()
        self._setup_hidden_fields()
    
    def _setup_client_fields(self):
        if 'client' in self.fields:
            self.fields['client'].widget = forms.HiddenInput()
            if self.instance and self.instance.client:
                self.fields['client'].initial = self.instance.client
        
        if self.instance and self.instance.client:
            client = self.instance.client
            client_fields = {
                'client_name': forms.CharField(
                    required=True,
                    max_length=255,
                    label='Nombre completo',
                    initial=client.full_name,
                    widget=forms.TextInput(attrs={
                        'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
                    })
                ),
                'client_dni': forms.CharField(
                    required=True,
                    max_length=20,
                    label='DNI/NIE',
                    initial=client.dni,
                    widget=forms.TextInput(attrs={
                        'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
                    })
                ),
                'client_gender': forms.ChoiceField(
                    required=True,
                    choices=Client.GenderChoices.choices,
                    label='Género',
                    initial=client.gender,
                    widget=forms.Select(attrs={
                        'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
                    })
                ),
                'client_email': forms.EmailField(
                    required=False,
                    label='Email',
                    initial=client.email,
                    widget=forms.EmailInput(attrs={
                        'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
                    })
                ),
                'client_phone': forms.CharField(
                    required=False,
                    max_length=20,
                    label='Teléfono',
                    initial=client.phone,
                    widget=forms.TextInput(attrs={
                        'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
                    })
                ),
                'client_notes': forms.CharField(
                    required=False,
                    label='Notas',
                    initial=client.notes,
                    widget=forms.Textarea(attrs={
                        'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white',
                        'rows': 3
                    })
                ),
            }
            
            new_fields = {}
            for field_name, field in client_fields.items():
                new_fields[field_name] = field
            for field_name, field in self.fields.items():
                new_fields[field_name] = field
            self.fields = new_fields
    
    def _setup_hidden_fields(self):
        if self.instance and self.instance.pk:
            if 'business_line' in self.fields:
                self.fields['business_line'].initial = self.instance.business_line
                self.fields['business_line'].widget = forms.HiddenInput()
            
            if 'category' in self.fields:
                self.fields['category'].initial = self.instance.category
                self.fields['category'].widget = forms.HiddenInput()
    
    def clean(self):
        cleaned_data = super().clean()
        
        ClientServiceFormValidator.validate_client_data(cleaned_data)
        
        if self.instance and self.instance.pk:
            new_dni = cleaned_data.get('client_dni', '').strip().upper()
            if new_dni and new_dni != self.instance.client.dni:
                if Client.objects.filter(dni=new_dni).exclude(pk=self.instance.client.pk).exists():
                    raise ValidationError({'client_dni': f'Ya existe otro cliente con el DNI {new_dni}'})
        
        return cleaned_data
    
    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)
        
        return ClientServiceTransactionManager.update_client_service(
            self.instance,
            self.cleaned_data
        )


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
