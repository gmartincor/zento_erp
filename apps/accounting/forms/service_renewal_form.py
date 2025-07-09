from django import forms
from django.core.exceptions import ValidationError
from datetime import timedelta, date

from .base_forms import BaseServiceForm, PaymentFieldsMixin, RemanenteFieldsMixin
from ..services.period_service import ServicePeriodManager
from ..services.payment_service import PaymentService


class ServiceRenewalForm(BaseServiceForm, PaymentFieldsMixin, RemanenteFieldsMixin):
    
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
        
        if self.client_service:
            self._set_minimum_date()
        
        self.add_payment_fields()
        self.add_remanente_fields()
        self._set_suggested_amount()
    
    def _set_minimum_date(self):
        last_period = ServicePeriodManager.get_last_period(self.client_service)
        
        if last_period:
            min_date = last_period.period_end + timedelta(days=1)
        elif self.client_service.start_date:
            min_date = self.client_service.start_date
        else:
            min_date = date.today()
        
        self.fields['end_date'].widget.attrs.update({
            'min': min_date.strftime('%Y-%m-%d')
        })
    
    def clean(self):
        cleaned_data = super().clean()
        
        end_date = cleaned_data.get('end_date')
        if self.client_service and end_date:
            last_period = ServicePeriodManager.get_last_period(self.client_service)
            if last_period and end_date <= last_period.period_end:
                raise ValidationError({
                    'end_date': 'La nueva fecha de fin debe ser posterior al último período existente'
                })
        
        renewal_type = cleaned_data.get('renewal_type')
        if renewal_type == 'with_payment':
            self.clean_payment_fields()
        else:
            for field in ['amount', 'payment_date', 'payment_method']:
                if field in self.errors:
                    del self.errors[field]
        return cleaned_data
    
    def save(self):
        renewal_type = self.cleaned_data['renewal_type']
        end_date = self.cleaned_data['end_date']
        notes = self.cleaned_data.get('notes', '')
        
        last_period = ServicePeriodManager.get_last_period(self.client_service)
        start_date = last_period.period_end + timedelta(days=1) if last_period else self.client_service.start_date
        
        period = ServicePeriodManager.create_period(
            client_service=self.client_service,
            period_start=start_date,
            period_end=end_date,
            notes=notes
        )
        
        if renewal_type == 'with_payment':
            period = PaymentService.process_payment(
                period=period,
                amount=self.cleaned_data['amount'],
                payment_date=self.cleaned_data['payment_date'],
                payment_method=self.cleaned_data['payment_method'],
                reference_number=self.cleaned_data.get('reference_number', ''),
                notes=f"Pago simultáneo con renovación",
                remanente=self.cleaned_data.get('remanente')
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
        
        last_period = ServicePeriodManager.get_last_period(self.client_service)
        period_start = last_period.period_end + timedelta(days=1) if last_period else self.client_service.start_date
        
        from ..models import ServicePayment
        temp_period = ServicePayment(
            client_service=self.client_service,
            period_start=period_start,
            period_end=end_date
        )
        
        suggested_amount = PaymentService.calculate_suggested_amount(
            temp_period, self.client_service
        )
        
        if 'amount' in self.fields:
            base_price = self.client_service.price
            if base_price and base_price > 0:
                self.fields['amount'].initial = base_price
                if suggested_amount and suggested_amount != base_price:
                    self.fields['amount'].help_text = f"Precio base: {base_price}€. Sugerido: {suggested_amount}€ (basado en pagos anteriores)"
                else:
                    self.fields['amount'].help_text = f"Precio base: {base_price}€"
            elif suggested_amount:
                self.fields['amount'].initial = suggested_amount
                self.fields['amount'].help_text = f"Sugerido: {suggested_amount}€ (basado en pagos anteriores)"
            
    def is_valid(self):
        is_valid = super().is_valid()
        renewal_type = self.data.get('renewal_type')
        
        if renewal_type != 'with_payment':
            payment_fields = ['amount', 'payment_date', 'payment_method']
            for field in payment_fields:
                if field in self.errors:
                    del self.errors[field]
            is_valid = len(self.errors) == 0
                    
        return is_valid
