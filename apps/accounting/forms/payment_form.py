from django import forms
from django.utils import timezone
from decimal import Decimal
from ..models import ServicePayment


class ServicePaymentForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'step': '0.01',
            'min': '0'
        }),
        label='Monto'
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
        label='Extender por (meses)'
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
        if service:
            self.fields['amount'].initial = service.price
