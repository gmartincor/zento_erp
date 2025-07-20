from django import forms
from django.utils import timezone
from decimal import Decimal
from ..models import ServicePayment
from ..services.payment_components import PaymentPeriodCalculator


class FlexiblePaymentForm(forms.Form):
    PAYMENT_TYPE_CHOICES = [
        ('extend', 'Pago con extensión del servicio'),
        ('custom_period', 'Pago por período específico'),
        ('no_extension', 'Pago sin extensión del servicio'),
    ]
    
    payment_type = forms.ChoiceField(
        choices=PAYMENT_TYPE_CHOICES,
        initial='extend',
        widget=forms.RadioSelect(attrs={
            'class': 'payment-type-selector'
        }),
        label='Tipo de pago'
    )
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'step': '0.01',
            'min': '0'
        }),
        label='Importe €'
    )
    
    payment_method = forms.ChoiceField(
        choices=ServicePayment.PaymentMethodChoices.choices,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Método de Pago'
    )
    
    payment_date = forms.DateField(
        initial=timezone.now().date,
        widget=forms.DateInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'type': 'date'
        }),
        label='Fecha de Pago'
    )
    
    extend_months = forms.IntegerField(
        initial=1,
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'min': '1',
            'max': '12'
        }),
        label='Extender por (meses)',
        required=False
    )
    
    period_start = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'type': 'date'
        }),
        label='Inicio del período',
        required=False
    )
    
    period_end = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'type': 'date'
        }),
        label='Fin del período',
        required=False
    )
    
    reference_number = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Número de referencia (opcional)'
        }),
        label='Referencia'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'rows': 3,
            'placeholder': 'Notas adicionales (opcional)'
        }),
        label='Notas'
    )
    
    def __init__(self, service=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = service
        
        if service:
            self.fields['amount'].initial = service.price
            
            next_period_start = PaymentPeriodCalculator.get_next_available_period_start(service)
            self.fields['period_start'].initial = next_period_start
    
    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        
        if payment_type == 'extend':
            extend_months = cleaned_data.get('extend_months')
            if not extend_months or extend_months < 1:
                raise forms.ValidationError({
                    'extend_months': 'Debe especificar los meses de extensión.'
                })
        
        elif payment_type == 'custom_period' or payment_type == 'no_extension':
            period_start = cleaned_data.get('period_start')
            period_end = cleaned_data.get('period_end')
            
            if not period_start:
                raise forms.ValidationError({
                    'period_start': 'Debe especificar la fecha de inicio del período.'
                })
            
            if not period_end:
                raise forms.ValidationError({
                    'period_end': 'Debe especificar la fecha de fin del período.'
                })
            
            if period_start and period_end and period_start >= period_end:
                raise forms.ValidationError({
                    'period_end': 'La fecha de fin debe ser posterior a la fecha de inicio.'
                })
        
        return cleaned_data
    
    def get_payment_data(self):
        payment_type = self.cleaned_data['payment_type']
        
        base_data = {
            'amount': self.cleaned_data['amount'],
            'payment_method': self.cleaned_data['payment_method'],
            'payment_date': self.cleaned_data['payment_date'],
            'reference_number': self.cleaned_data.get('reference_number'),
            'notes': self.cleaned_data.get('notes'),
        }
        
        if payment_type == 'extend':
            base_data.update({
                'extend_months': self.cleaned_data['extend_months'],
                'extend_service': True
            })
        elif payment_type == 'custom_period':
            base_data.update({
                'period_start': self.cleaned_data['period_start'],
                'period_end': self.cleaned_data['period_end'],
                'extend_service': True
            })
        elif payment_type == 'no_extension':
            base_data.update({
                'period_start': self.cleaned_data['period_start'],
                'period_end': self.cleaned_data['period_end'],
                'extend_service': False
            })
        
        return payment_type, base_data
