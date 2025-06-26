from django import forms
from django.utils import timezone
from ..models import ServicePayment


class ServiceActionForm(forms.Form):
    
    action_type = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect(attrs={
            'class': 'text-blue-600 focus:ring-blue-500'
        }),
        label='Acción a realizar'
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'type': 'date'
        }),
        label='Fecha de Inicio (solo para renovación)'
    )
    
    duration_months = forms.IntegerField(
        initial=1,
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'min': '1',
            'max': '12'
        }),
        label='Duración (meses)'
    )
    
    amount = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'step': '0.01',
            'min': '0'
        }),
        label='Monto'
    )
    
    payment_now = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
        }),
        label='Registrar pago ahora'
    )
    
    payment_method = forms.ChoiceField(
        choices=ServicePayment.PaymentMethodChoices.choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Método de Pago'
    )
    
    payment_date = forms.DateField(
        required=False,
        initial=timezone.now().date,
        widget=forms.DateInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'type': 'date'
        }),
        label='Fecha de Pago'
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
            'placeholder': 'Notas adicionales'
        }),
        label='Notas'
    )
    
    no_renew_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'rows': 2,
            'placeholder': 'Motivo por el cual no se renueva (opcional)'
        }),
        label='Motivo de no renovación'
    )
    
    def __init__(self, *args, service=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if service:
            self.service = service
            self.fields['amount'].initial = service.price
            
            action_choices = [
                ('extend', 'Extender servicio sin pago'),
                ('payment_standalone', 'Registrar pago sin extensión'),
                ('payment_and_extend', 'Pago y extensión simultáneos'),
            ]
            
            self.fields['action_type'].choices = action_choices
    
    def clean(self):
        cleaned_data = super().clean()
        action_type = cleaned_data.get('action_type')
        payment_now = cleaned_data.get('payment_now')
        payment_method = cleaned_data.get('payment_method')
        amount = cleaned_data.get('amount')
        
        if action_type in ['payment_standalone', 'payment_and_extend']:
            if not amount:
                raise forms.ValidationError('El monto es requerido para acciones de pago.')
            
            if payment_now and not payment_method:
                raise forms.ValidationError('Debe seleccionar un método de pago si registra el pago ahora.')
        
        return cleaned_data
