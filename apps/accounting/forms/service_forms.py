from django import forms
from django.core.exceptions import ValidationError

from apps.accounting.models import Client, ClientService
from apps.business_lines.models import BusinessLine
from apps.accounting.services.business_line_service import BusinessLineService
from apps.accounting.services.client_service import ClientServiceOperations
from apps.accounting.services.validation_service import ValidationService


class BaseClientServiceForm(forms.ModelForm):
    class Meta:
        model = ClientService
        fields = [
            'client', 'business_line', 'category', 'price', 
            'payment_method', 'start_date', 'renewal_date', 'remanentes'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
            }),
            'renewal_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
            }),
            'price': forms.NumberInput(attrs={
                'step': '0.01', 
                'min': '0',
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
            'payment_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.business_line = kwargs.pop('business_line', None)
        self.category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)
        self._setup_form_fields()
        self._apply_field_styling()
    
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
            
        self._enhance_field_metadata()
    
    def _apply_field_styling(self):
        # Clases base para todos los campos
        base_input_classes = (
            'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 '
            'rounded-md shadow-sm focus:outline-none focus:ring-primary-500 '
            'focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        )
        
        # Clases específicas por tipo de widget
        widget_classes = {
            forms.TextInput: base_input_classes,
            forms.EmailInput: base_input_classes,
            forms.NumberInput: base_input_classes,
            forms.DateInput: base_input_classes,
            forms.Select: base_input_classes,
            forms.Textarea: base_input_classes,
            forms.CheckboxInput: 'mr-2',
        }
        
        for field_name, field in self.fields.items():
            widget_type = type(field.widget)
            if widget_type in widget_classes:
                field.widget.attrs['class'] = widget_classes[widget_type]
            else:
                field.widget.attrs['class'] = base_input_classes
    
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
            'price': {
                'help_text': 'Precio del servicio en euros'
            },
            'payment_method': {
                'help_text': 'Método de pago utilizado por el cliente'
            },
            'start_date': {
                'help_text': 'Fecha de inicio del servicio'
            },
            'renewal_date': {
                'help_text': 'Fecha de renovación (opcional)'
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
        
        if hasattr(self, '_get_temp_client_for_validation'):
            client = self._get_temp_client_for_validation()
        else:
            client = cleaned_data.get('client')
        
        business_line = cleaned_data.get('business_line')
        category = cleaned_data.get('category')
        remanentes = cleaned_data.get('remanentes')
        
        if not business_line:
            self.add_error('business_line', 'Este campo es requerido.')
        
        if not category:
            self.add_error('category', 'Este campo es requerido.')
        
        if business_line and category:
            try:
                self._validate_business_rules(
                    client, business_line, category, remanentes
                )
            except ValidationError as e:
                if hasattr(e, 'error_dict'):
                    for field, errors in e.error_dict.items():
                        self.add_error(field, errors)
                else:
                    self.add_error(None, str(e))
        
        return cleaned_data
    
    def _validate_business_rules(self, client, business_line, category, remanentes):
        pass


class ClientServiceCreateForm(BaseClientServiceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_client_creation_fields()
        self.fields.pop('client', None)
    
    def _add_client_creation_fields(self):
        input_classes = (
            'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 '
            'rounded-md shadow-sm focus:outline-none focus:ring-primary-500 '
            'focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        )
        
        self.fields['client_name'] = forms.CharField(
            required=True,
            max_length=255,
            label='Nombre completo',
            help_text='Nombre completo del cliente',
            widget=forms.TextInput(attrs={'class': input_classes})
        )
        self.fields['client_dni'] = forms.CharField(
            required=True,
            max_length=20,
            label='DNI/NIE',
            help_text='Documento de identidad del cliente',
            widget=forms.TextInput(attrs={'class': input_classes})
        )
        self.fields['client_gender'] = forms.ChoiceField(
            required=True,
            choices=Client.GenderChoices.choices,
            label='Género',
            widget=forms.Select(attrs={'class': input_classes})
        )
        self.fields['client_email'] = forms.EmailField(
            required=False,
            label='Email',
            widget=forms.EmailInput(attrs={'class': input_classes})
        )
        self.fields['client_phone'] = forms.CharField(
            required=False,
            max_length=20,
            label='Teléfono',
            widget=forms.TextInput(attrs={'class': input_classes})
        )
    
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
        
        # Check for existing active service (only if we have a real client with ID)
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
                price=self.cleaned_data['price'],
                payment_method=self.cleaned_data['payment_method'],
                start_date=self.cleaned_data['start_date'],
                renewal_date=self.cleaned_data.get('renewal_date'),
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
            phone=self.cleaned_data.get('client_phone', '')
        )


class ClientServiceUpdateForm(BaseClientServiceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hide_client_field()
        self._add_client_edit_fields()
    
    def get_initial(self):
        initial = super().get_initial()
        if self.instance and self.instance.pk:
            initial.update({
                'price': self.instance.price,
                'payment_method': self.instance.payment_method,
                'start_date': self.instance.start_date,
                'renewal_date': self.instance.renewal_date,
                'remanentes': self.instance.remanentes
            })
        return initial
    
    def _hide_client_field(self):
        if 'client' in self.fields:
            self.fields['client'].widget = forms.HiddenInput()
            if self.instance and self.instance.client:
                self.fields['client'].initial = self.instance.client
    
    def _add_client_edit_fields(self):
        input_classes = (
            'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 '
            'rounded-md shadow-sm focus:outline-none focus:ring-primary-500 '
            'focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        )
        
        if self.instance and self.instance.client:
            client = self.instance.client
            
            self.fields['client_name'] = forms.CharField(
                max_length=255,
                label='Nombre completo',
                initial=client.full_name,
                widget=forms.TextInput(attrs={'class': input_classes})
            )
            self.fields['client_dni'] = forms.CharField(
                max_length=20,
                label='DNI/NIE',
                initial=client.dni,
                widget=forms.TextInput(attrs={'class': input_classes})
            )
            self.fields['client_gender'] = forms.ChoiceField(
                choices=Client.GenderChoices.choices,
                label='Género',
                initial=client.gender,
                widget=forms.Select(attrs={'class': input_classes})
            )
            self.fields['client_email'] = forms.EmailField(
                required=False,
                label='Email',
                initial=client.email,
                widget=forms.EmailInput(attrs={'class': input_classes})
            )
            self.fields['client_phone'] = forms.CharField(
                required=False,
                max_length=20,
                label='Teléfono',
                initial=client.phone,
                widget=forms.TextInput(attrs={'class': input_classes})
            )
    
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
            self._update_client_data()
            
            service = self.instance
            service.price = self.cleaned_data['price']
            service.payment_method = self.cleaned_data['payment_method']
            service.start_date = self.cleaned_data['start_date']
            service.renewal_date = self.cleaned_data.get('renewal_date')
            service.remanentes = self.cleaned_data.get('remanentes', {})
            
            service.save()
            return service
        return super().save(commit=False)
    
    def _update_client_data(self):
        if self.instance and self.instance.client:
            client = self.instance.client
            client.full_name = self.cleaned_data.get('client_name', client.full_name)
            client.dni = self.cleaned_data.get('client_dni', client.dni)
            client.gender = self.cleaned_data.get('client_gender', client.gender)
            client.email = self.cleaned_data.get('client_email', client.email)
            client.phone = self.cleaned_data.get('client_phone', client.phone)
            client.save()


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
    payment_method = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los métodos')] + ClientService.PaymentMethodChoices.choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
