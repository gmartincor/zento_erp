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
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'renewal_date': forms.DateInput(attrs={'type': 'date'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'remanentes': forms.Textarea(attrs={'rows': 3}),
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
            self.fields['business_line'].widget.attrs['readonly'] = True
        if self.category:
            self.fields['category'].initial = self.category
            self.fields['category'].widget.attrs['readonly'] = True
        self._enhance_field_metadata()
    
    def _apply_field_styling(self):
        base_classes = (
            'form-control bg-white border border-gray-300 text-gray-900 '
            'text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 '
            'block w-full p-2.5'
        )
        for field_name, field in self.fields.items():
            current_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{current_classes} {base_classes}".strip()
            if field.required:
                field.widget.attrs['class'] += ' border-red-500'
    
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
        client = cleaned_data.get('client')
        business_line = cleaned_data.get('business_line')
        category = cleaned_data.get('category')
        remanentes = cleaned_data.get('remanentes')
        if client and business_line and category:
            try:
                self._validate_business_rules(
                    client, business_line, category, remanentes
                )
            except ValidationError as e:
                if hasattr(e, 'error_dict'):
                    for field, errors in e.error_dict.items():
                        self.add_error(field, errors)
                else:
                    raise forms.ValidationError(str(e))
        return cleaned_data
    
    def _validate_business_rules(self, client, business_line, category, remanentes):
        pass


class ClientServiceCreateForm(BaseClientServiceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_client_creation_fields()
    
    def _add_client_creation_fields(self):
        self.fields['create_new_client'] = forms.BooleanField(
            required=False,
            label='Crear nuevo cliente',
            help_text='Marcar para crear un nuevo cliente'
        )
        self.fields['new_client_name'] = forms.CharField(
            required=False,
            max_length=255,
            label='Nombre completo',
            help_text='Nombre completo del nuevo cliente'
        )
        self.fields['new_client_dni'] = forms.CharField(
            required=False,
            max_length=20,
            label='DNI/NIE',
            help_text='Documento de identidad del nuevo cliente'
        )
        self.fields['new_client_gender'] = forms.ChoiceField(
            required=False,
            choices=Client.GenderChoices.choices,
            label='Género'
        )
        self.fields['new_client_email'] = forms.EmailField(
            required=False,
            label='Email'
        )
        self.fields['new_client_phone'] = forms.CharField(
            required=False,
            max_length=20,
            label='Teléfono'
        )
    
    def clean(self):
        cleaned_data = super().clean()
        create_new = cleaned_data.get('create_new_client')
        client = cleaned_data.get('client')
        if create_new:
            self._validate_new_client_fields(cleaned_data)
            cleaned_data['client'] = None
        elif not client:
            raise forms.ValidationError(
                'Debe seleccionar un cliente o crear uno nuevo.'
            )
        return cleaned_data
    
    def _validate_new_client_fields(self, cleaned_data):
        required_fields = ['new_client_name', 'new_client_dni', 'new_client_gender']
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, 'Este campo es obligatorio para crear un nuevo cliente.')
        dni = cleaned_data.get('new_client_dni')
        if dni and Client.objects.filter(dni=dni, is_deleted=False).exists():
            self.add_error('new_client_dni', f'Ya existe un cliente con DNI {dni}')
    
    def _validate_business_rules(self, client, business_line, category, remanentes):
        client_service_ops = ClientServiceOperations()
        client_service_ops._validate_service_creation(
            client, business_line, category, remanentes
        )
    
    def save(self, commit=True):
        if self.cleaned_data.get('create_new_client'):
            client = self._create_new_client()
            self.instance.client = client
        if commit:
            client_service_ops = ClientServiceOperations()
            return client_service_ops.create_client_service(
                client=self.instance.client,
                business_line=self.instance.business_line,
                category=self.instance.category,
                price=self.instance.price,
                payment_method=self.instance.payment_method,
                start_date=self.instance.start_date,
                renewal_date=self.instance.renewal_date,
                remanentes=self.instance.remanentes
            )
        return self.instance
    
    def _create_new_client(self):
        client_service_ops = ClientServiceOperations()
        return client_service_ops.create_client(
            full_name=self.cleaned_data['new_client_name'],
            dni=self.cleaned_data['new_client_dni'],
            gender=self.cleaned_data['new_client_gender'],
            email=self.cleaned_data.get('new_client_email', ''),
            phone=self.cleaned_data.get('new_client_phone', '')
        )


class ClientServiceUpdateForm(BaseClientServiceForm):
    def _validate_business_rules(self, client, business_line, category, remanentes):
        client_service_ops = ClientServiceOperations()
        temp_service = ClientService(
            client=client,
            business_line=business_line,
            category=category,
            remanentes=remanentes
        )
        client_service_ops._validate_service_update(temp_service)
    
    def save(self, commit=True):
        if commit:
            client_service_ops = ClientServiceOperations()
            return client_service_ops.update_client_service(
                service=self.instance,
                **self.cleaned_data
            )
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
