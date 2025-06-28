from django import forms
from django.core.exceptions import ValidationError
from datetime import date

from .base_forms import PaymentFieldsMixin
from ..models import ServicePayment
from ..services.deferred_payment_service import DeferredPaymentService


class DeferredPaymentForm(PaymentFieldsMixin, forms.Form):
    
    period = forms.ModelChoiceField(
        queryset=ServicePayment.objects.none(),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500'
        }),
        label="Período a pagar",
        help_text="Selecciona el período que deseas pagar"
    )
    
    def __init__(self, client_service=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_service = client_service
        self.add_payment_fields()
        
        if client_service:
            self._setup_period_choices()
    
    def _setup_period_choices(self):
        pending_periods = DeferredPaymentService.get_pending_periods_for_payment(self.client_service)
        
        if not pending_periods.exists():
            self.fields['period'].queryset = ServicePayment.objects.none()
            self.fields['period'].help_text = "No hay períodos pendientes de pago"
            for field in self.fields.values():
                if hasattr(field, 'disabled'):
                    field.disabled = True
        else:
            self.fields['period'].queryset = pending_periods
    
    def clean(self):
        cleaned_data = super().clean()
        
        period = cleaned_data.get('period')
        payment_date = cleaned_data.get('payment_date')
        
        if period and payment_date:
            can_pay, reason = DeferredPaymentService.can_pay_period(period, payment_date)
            if not can_pay:
                raise ValidationError({'payment_date': reason})
        
        self.clean_payment_fields()
        return cleaned_data
    
    def save(self):
        return DeferredPaymentService.process_deferred_payment(
            period=self.cleaned_data['period'],
            amount=self.cleaned_data['amount'],
            payment_date=self.cleaned_data['payment_date'],
            payment_method=self.cleaned_data['payment_method'],
            reference_number=self.cleaned_data.get('reference_number', ''),
            notes=self.cleaned_data.get('notes', '')
        )
