from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from ..models import ServicePayment, ClientService


class BaseServiceForm(forms.Form):
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white',
            'placeholder': 'Notas adicionales (opcional)'
        }),
        label="Notas"
    )
    
    def __init__(self, client_service=None, *args, **kwargs):
        self.client_service = client_service
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.client_service:
            raise ValidationError("Se requiere un servicio válido")
        
        return cleaned_data


class PaymentFieldsMixin:
    
    def add_payment_fields(self):
        base_input_class = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        
        self.fields['amount'] = forms.DecimalField(
            max_digits=10,
            decimal_places=2,
            min_value=Decimal('0.01'),
            widget=forms.NumberInput(attrs={
                'class': base_input_class,
                'step': '0.01',
                'placeholder': '0.00'
            }),
            label="Monto"
        )
        
        self.fields['payment_date'] = forms.DateField(
            initial=timezone.now().date(),
            widget=forms.DateInput(attrs={
                'type': 'date',
                'class': base_input_class
            }),
            label="Fecha de pago"
        )
        
        self.fields['payment_method'] = forms.ChoiceField(
            choices=ServicePayment.PaymentMethodChoices.choices,
            widget=forms.Select(attrs={'class': base_input_class}),
            label="Método de pago"
        )
        
        self.fields['reference_number'] = forms.CharField(
            required=False,
            max_length=100,
            widget=forms.TextInput(attrs={
                'class': base_input_class,
                'placeholder': 'Número de referencia (opcional)'
            }),
            label="Referencia"
        )
    
    def clean_payment_fields(self):
        cleaned_data = self.cleaned_data
        
        payment_date = cleaned_data.get('payment_date')
        amount = cleaned_data.get('amount')
        
        if payment_date and payment_date > timezone.now().date():
            raise ValidationError({
                'payment_date': 'La fecha de pago no puede ser futura'
            })
        
        if amount and amount <= 0:
            raise ValidationError({
                'amount': 'El monto debe ser mayor a cero'
            })
        
        return cleaned_data


class PeriodFieldsMixin:
    
    def add_period_fields(self, show_duration=True):
        base_input_class = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        
        if show_duration:
            self.fields['duration_months'] = forms.IntegerField(
                min_value=1,
                max_value=24,
                initial=1,
                widget=forms.NumberInput(attrs={
                    'class': base_input_class,
                    'min': '1',
                    'max': '24'
                }),
                label="Duración (meses)"
            )
        else:
            self.fields['period_start'] = forms.DateField(
                widget=forms.DateInput(attrs={
                    'type': 'date',
                    'class': base_input_class
                }),
                label="Inicio del período"
            )
            
            self.fields['period_end'] = forms.DateField(
                widget=forms.DateInput(attrs={
                    'type': 'date',
                    'class': base_input_class
                }),
                label="Fin del período"
            )
    
    def clean_period_fields(self):
        cleaned_data = super().clean()
        
        period_start = cleaned_data.get('period_start')
        period_end = cleaned_data.get('period_end')
        
        if period_start and period_end and period_start >= period_end:
            raise ValidationError({
                'period_end': 'La fecha de fin debe ser posterior a la fecha de inicio'
            })
        
        return cleaned_data


class RemanenteFieldsMixin:
    
    def add_remanente_fields(self):
        if not (self.client_service and self.client_service.business_line.allows_remanentes):
            return
            
        available_types = self.client_service.business_line.get_available_remanente_types()
        if not available_types.exists():
            return
            
        from ..services.period_service import ServicePeriodManager
        pending_periods = ServicePeriodManager.get_pending_periods(self.client_service)
        
        base_input_class = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        
        for period in pending_periods:
            period_id = period.id
            
            self.fields[f'enable_remanente_{period_id}'] = forms.BooleanField(
                required=False,
                widget=forms.CheckboxInput(attrs={
                    'class': 'text-primary-600 focus:ring-primary-500 border-gray-300 rounded',
                }),
                label=f"Aplicar remanente al período {period.period_start.strftime('%d/%m/%Y')} - {period.period_end.strftime('%d/%m/%Y')}"
            )
            
            self.fields[f'remanente_type_{period_id}'] = forms.ModelChoiceField(
                queryset=available_types,
                required=False,
                empty_label="Seleccionar tipo de remanente",
                widget=forms.Select(attrs={'class': base_input_class}),
                label="Tipo de remanente"
            )
            
            # Campo de monto - siguiendo el patrón de amount
            self.fields[f'remanente_amount_{period_id}'] = forms.DecimalField(
                required=False,
                max_digits=10,
                decimal_places=2,
                min_value=Decimal('0.01'),
                widget=forms.NumberInput(attrs={
                    'class': base_input_class,
                    'step': '0.01',
                    'placeholder': '0.00'
                }),
                label="Monto (€)"
            )
            
            # Campo de notas - siguiendo el patrón de notes en BaseServiceForm
            self.fields[f'remanente_notes_{period_id}'] = forms.CharField(
                required=False,
                max_length=500,
                widget=forms.Textarea(attrs={
                    'rows': 2,
                    'class': base_input_class,
                    'placeholder': 'Motivo o descripción del remanente...'
                }),
                label="Notas"
            )
    
    def clean_remanente_fields(self):
        """Valida campos de remanentes siguiendo el patrón de otros mixins"""
        cleaned_data = self.cleaned_data
        
        if not (self.client_service and self.client_service.business_line.allows_remanentes):
            return cleaned_data
            
        errors = {}
        
        for field_name, value in cleaned_data.items():
            if field_name.startswith('enable_remanente_') and value:
                period_id = field_name.split('_')[-1]
                
                # Validar tipo de remanente
                tipo_field = f'remanente_type_{period_id}'
                if not cleaned_data.get(tipo_field):
                    errors[tipo_field] = 'Debe seleccionar un tipo de remanente.'
                
                # Validar monto
                monto_field = f'remanente_amount_{period_id}'
                amount = cleaned_data.get(monto_field)
                if not amount:
                    errors[monto_field] = 'Debe especificar un monto válido.'
                elif amount <= 0:
                    errors[monto_field] = 'El monto debe ser mayor a cero.'
        
        if errors:
            raise ValidationError(errors)
            
        return cleaned_data
    
    def save_remanentes(self, user):
        """Guarda los remanentes configurados usando los servicios existentes"""
        if not (self.client_service and self.client_service.business_line.allows_remanentes):
            return []
            
        from apps.business_lines.models import ServicePeriodRemanente
        from ..services.period_service import ServicePeriodManager
        
        pending_periods = ServicePeriodManager.get_pending_periods(self.client_service)
        created_remanentes = []
        
        for period in pending_periods:
            period_id = period.id
            
            if self.cleaned_data.get(f'enable_remanente_{period_id}'):
                remanente = ServicePeriodRemanente.objects.create(
                    client_service=self.client_service,
                    period_start=period.period_start,
                    period_end=period.period_end,
                    remanente_type=self.cleaned_data[f'remanente_type_{period_id}'],
                    amount=self.cleaned_data[f'remanente_amount_{period_id}'],
                    notes=self.cleaned_data.get(f'remanente_notes_{period_id}', ''),
                    created_by=user
                )
                created_remanentes.append(remanente)
        
        return created_remanentes
