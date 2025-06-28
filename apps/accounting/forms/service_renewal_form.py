from django import forms
from django.core.exceptions import ValidationError

from .base_forms import BaseServiceForm, PaymentFieldsMixin, PeriodFieldsMixin
from ..services.period_service import ServicePeriodManager
from ..services.payment_service import PaymentService


class ServiceRenewalForm(BaseServiceForm, PaymentFieldsMixin, PeriodFieldsMixin):
    
    RENEWAL_TYPE_CHOICES = [
        ('period_only', 'Solo extender servicio (sin pago)'),
        ('with_payment', 'Extender servicio y procesar pago')
    ]
    
    renewal_type = forms.ChoiceField(
        choices=RENEWAL_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 focus:ring-primary-500 dark:focus:ring-primary-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600'
        }),
        label="Tipo de renovación",
        initial='period_only'
    )
    
    def __init__(self, client_service=None, *args, **kwargs):
        super().__init__(client_service=client_service, *args, **kwargs)
        self.add_period_fields(show_duration=True)
        
        renewal_type = self.data.get('renewal_type', self.initial.get('renewal_type', 'period_only'))
        if renewal_type == 'with_payment':
            self.add_payment_fields()
            self._set_suggested_amount()
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.client_service or not self.client_service.end_date:
            raise ValidationError("No se puede renovar un servicio sin fecha de fin")
        
        renewal_type = cleaned_data.get('renewal_type')
        if renewal_type == 'with_payment':
            self.clean_payment_fields()
        return cleaned_data
    
    def save(self):
        renewal_type = self.cleaned_data['renewal_type']
        duration_months = self.cleaned_data['duration_months']
        notes = self.cleaned_data.get('notes', '')
        
        if renewal_type == 'period_only':
            period = ServicePeriodManager.extend_service(
                client_service=self.client_service,
                extension_months=duration_months,
                notes=notes
            )
        elif renewal_type == 'with_payment':
            period = ServicePeriodManager.extend_service(
                client_service=self.client_service,
                extension_months=duration_months,
                notes=notes
            )
            period = PaymentService.process_payment(
                period=period,
                amount=self.cleaned_data['amount'],
                payment_date=self.cleaned_data['payment_date'],
                payment_method=self.cleaned_data['payment_method'],
                reference_number=self.cleaned_data.get('reference_number', ''),
                notes=f"Pago simultáneo con renovación"
            )
        
        return period
    
    def _set_suggested_amount(self):
        if not self.client_service or not self.client_service.end_date:
            return
        
        from datetime import timedelta
        current_end = self.client_service.end_date
        temp_start = current_end + timedelta(days=1)
        temp_end = temp_start + timedelta(days=30)
        
        from ..models import ServicePayment
        temp_period = ServicePayment(
            client_service=self.client_service,
            period_start=temp_start,
            period_end=temp_end
        )
        
        suggested_amount = PaymentService.calculate_suggested_amount(
            temp_period, self.client_service
        )
        
        if suggested_amount and 'amount' in self.fields:
            self.fields['amount'].initial = suggested_amount
            self.fields['amount'].help_text = f"Sugerido: {suggested_amount}€ (basado en pagos anteriores)"
