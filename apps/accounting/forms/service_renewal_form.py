from django import forms
from django.core.exceptions import ValidationError
from datetime import timedelta

from .base_forms import BaseServiceForm, PaymentFieldsMixin
from ..services.period_service import ServicePeriodManager
from ..services.payment_service import PaymentService


class ServiceRenewalForm(BaseServiceForm, PaymentFieldsMixin):
    
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
    
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        }),
        label="Fecha de finalización"
    )
    
    def __init__(self, client_service=None, *args, **kwargs):
        super().__init__(client_service=client_service, *args, **kwargs)
        
        if self.client_service and self.client_service.end_date:
            from datetime import timedelta
            min_date = self.client_service.end_date + timedelta(days=1)
            self.fields['end_date'].widget.attrs.update({
                'min': min_date.strftime('%Y-%m-%d')
            })
        
        renewal_type = self.data.get('renewal_type', self.initial.get('renewal_type', 'period_only'))
        if renewal_type == 'with_payment':
            self.add_payment_fields()
            self._set_suggested_amount()
    
    def clean(self):
        cleaned_data = super().clean()
        
        end_date = cleaned_data.get('end_date')
        if self.client_service and self.client_service.end_date and end_date:
            if end_date <= self.client_service.end_date:
                raise ValidationError({
                    'end_date': 'La nueva fecha de fin debe ser posterior a la fecha actual de finalización'
                })
        
        renewal_type = cleaned_data.get('renewal_type')
        if renewal_type == 'with_payment':
            self.clean_payment_fields()
        return cleaned_data
    
    def save(self):
        renewal_type = self.cleaned_data['renewal_type']
        end_date = self.cleaned_data['end_date']
        notes = self.cleaned_data.get('notes', '')
        
        if renewal_type == 'period_only':
            period = ServicePeriodManager.extend_service_to_date(
                client_service=self.client_service,
                new_end_date=end_date,
                notes=notes
            )
        elif renewal_type == 'with_payment':
            period = ServicePeriodManager.extend_service_to_date(
                client_service=self.client_service,
                new_end_date=end_date,
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
        if not self.client_service:
            return
        
        end_date = self.data.get('end_date')
        if not end_date:
            return
            
        try:
            from datetime import datetime
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return
        
        if self.client_service.end_date:
            period_start = self.client_service.end_date + timedelta(days=1)
        else:
            period_start = self.client_service.start_date or end_date
        
        from ..models import ServicePayment
        temp_period = ServicePayment(
            client_service=self.client_service,
            period_start=period_start,
            period_end=end_date
        )
        
        suggested_amount = PaymentService.calculate_suggested_amount(
            temp_period, self.client_service
        )
        
        if suggested_amount and 'amount' in self.fields:
            self.fields['amount'].initial = suggested_amount
            self.fields['amount'].help_text = f"Sugerido: {suggested_amount}€ (basado en pagos anteriores)"
