from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from ..models import ServicePayment, ClientService
from apps.core.form_utils import apply_currency_field_styles


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
            label="Importe €"
        )
        
        apply_currency_field_styles(self.fields['amount'], base_input_class)
        
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
                'amount': 'El importe debe ser mayor a cero'
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
        if hasattr(self, 'client_service') and self.client_service and self.client_service.category != 'business':
            return
            
        base_input_class = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        
        self.fields['remanente'] = forms.DecimalField(
            max_digits=10,
            decimal_places=2,
            required=False,
            widget=forms.NumberInput(attrs={
                'class': base_input_class,
                'step': '0.01',
                'placeholder': '0.00'
            }),
            label="Remanente",
            help_text="Valor positivo o negativo a aplicar al período"
        )
