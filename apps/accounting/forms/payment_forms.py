from typing import Dict, Any, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounting.models import ServicePayment, ClientService
from apps.accounting.services.payment_service import PaymentService


class PaymentBaseForm(forms.ModelForm):
    class Meta:
        model = ServicePayment
        fields = [
            'amount', 'payment_date', 'period_start', 'period_end',
            'payment_method', 'reference_number', 'notes'
        ]
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'period_start': forms.DateInput(attrs={'type': 'date'}),
            'period_end': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        self.client_service = kwargs.pop('client_service', None)
        super().__init__(*args, **kwargs)
        self._setup_field_styles()
        self._setup_defaults()

    def _setup_field_styles(self):
        base_class = 'form-control bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5'
        
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': base_class,
                    'placeholder': f'Introduce {field.label.lower()}...'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': base_class.replace('p-2.5', 'p-2')
                })
            else:
                field.widget.attrs.update({
                    'class': base_class,
                    'placeholder': f'Introduce {field.label.lower()}...'
                })

    def _setup_defaults(self):
        if not self.instance.pk:
            self.fields['payment_date'].initial = timezone.now().date()
            
            if self.client_service:
                next_start = PaymentService.get_next_renewal_date(self.client_service)
                if next_start:
                    self.fields['period_start'].initial = next_start

    def clean(self):
        cleaned_data = super().clean()
        period_start = cleaned_data.get('period_start')
        period_end = cleaned_data.get('period_end')
        payment_date = cleaned_data.get('payment_date')

        if period_start and period_end:
            if period_start >= period_end:
                raise ValidationError({
                    'period_end': 'La fecha de fin debe ser posterior a la fecha de inicio.'
                })

        if payment_date and period_end:
            if payment_date > period_end:
                raise ValidationError({
                    'payment_date': 'La fecha de pago no puede ser posterior al fin del período.'
                })

        if self.client_service and period_start and period_end:
            if not PaymentService.validate_payment_period(self.client_service, period_start, period_end):
                raise ValidationError(
                    'El período seleccionado se superpone con otro pago existente.'
                )

        return cleaned_data


class RenewalForm(PaymentBaseForm):
    duration_months = forms.IntegerField(
        label='Duración (meses)',
        min_value=1,
        max_value=24,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '24'})
    )

    class Meta(PaymentBaseForm.Meta):
        fields = ['amount', 'duration_months', 'payment_method', 'payment_date', 'reference_number', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if 'period_start' in self.fields:
            del self.fields['period_start']
        if 'period_end' in self.fields:
            del self.fields['period_end']

    def clean(self):
        cleaned_data = super().clean()
        duration_months = cleaned_data.get('duration_months')
        payment_date = cleaned_data.get('payment_date')

        if duration_months and payment_date and self.client_service:
            next_start = PaymentService.get_next_renewal_date(self.client_service)
            start_date = next_start if next_start else payment_date
            
            end_date = PaymentService._calculate_period_end(start_date, duration_months)
            
            cleaned_data['period_start'] = start_date
            cleaned_data['period_end'] = end_date

        return cleaned_data

    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)

        duration_months = self.cleaned_data['duration_months']
        
        return PaymentService.process_renewal(
            client_service=self.client_service,
            amount=self.cleaned_data['amount'],
            duration_months=duration_months,
            payment_method=self.cleaned_data['payment_method'],
            payment_date=self.cleaned_data.get('payment_date'),
            reference_number=self.cleaned_data.get('reference_number', ''),
            notes=self.cleaned_data.get('notes', '')
        )


class PaymentCreateForm(PaymentBaseForm):
    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)

        return PaymentService.create_payment(
            client_service=self.client_service,
            amount=self.cleaned_data['amount'],
            period_start=self.cleaned_data['period_start'],
            period_end=self.cleaned_data['period_end'],
            payment_method=self.cleaned_data['payment_method'],
            payment_date=self.cleaned_data.get('payment_date'),
            reference_number=self.cleaned_data.get('reference_number', ''),
            notes=self.cleaned_data.get('notes', ''),
            mark_as_paid=True
        )


class PaymentUpdateForm(PaymentBaseForm):
    class Meta(PaymentBaseForm.Meta):
        fields = PaymentBaseForm.Meta.fields + ['status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.status == ServicePayment.StatusChoices.PAID:
            for field_name in ['period_start', 'period_end', 'amount']:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs['readonly'] = True


class PaymentFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'Todos los estados')] + list(ServicePayment.StatusChoices.choices)
    METHOD_CHOICES = [('', 'Todos los métodos')] + list(ServicePayment.PaymentMethodChoices.choices)
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label='Estado'
    )
    
    payment_method = forms.ChoiceField(
        choices=METHOD_CHOICES,
        required=False,
        label='Método de pago'
    )
    
    date_from = forms.DateField(
        required=False,
        label='Desde',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    date_to = forms.DateField(
        required=False,
        label='Hasta',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    amount_from = forms.DecimalField(
        required=False,
        label='Monto mínimo',
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0'})
    )
    
    amount_to = forms.DecimalField(
        required=False,
        label='Monto máximo',
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_field_styles()

    def _setup_field_styles(self):
        base_class = 'form-control bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5'
        
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': base_class.replace('p-2.5', 'p-2')
                })
            else:
                field.widget.attrs.update({
                    'class': base_class
                })

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        amount_from = cleaned_data.get('amount_from')
        amount_to = cleaned_data.get('amount_to')

        if date_from and date_to and date_from > date_to:
            raise ValidationError({
                'date_to': 'La fecha final debe ser posterior a la fecha inicial.'
            })

        if amount_from and amount_to and amount_from > amount_to:
            raise ValidationError({
                'amount_to': 'El monto máximo debe ser mayor al monto mínimo.'
            })

        return cleaned_data
