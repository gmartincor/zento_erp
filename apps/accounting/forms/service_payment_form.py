from django import forms
from django.core.exceptions import ValidationError

from .base_forms import BaseServiceForm, PaymentFieldsMixin
from ..services.payment_service import PaymentService
from ..models import ServicePayment


class ServicePaymentForm(BaseServiceForm, PaymentFieldsMixin):
    
    period = forms.ModelChoiceField(
        queryset=ServicePayment.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Período a pagar",
        help_text="Selecciona el período al que corresponde este pago"
    )
    
    def __init__(self, client_service=None, *args, **kwargs):
        super().__init__(client_service=client_service, *args, **kwargs)
        self.add_payment_fields()
        if self.client_service:
            self._setup_period_choices()
        self._setup_dynamic_amount()
    
    def clean(self):
        cleaned_data = super().clean()
        self.clean_payment_fields()
        period = cleaned_data.get('period')
        if period and not period.can_be_paid:
            raise ValidationError({
                'period': f'El período seleccionado no puede recibir pagos (estado: {period.get_status_display()})'
            })
        return cleaned_data
    
    def save(self):
        return PaymentService.process_payment(
            period=self.cleaned_data['period'],
            amount=self.cleaned_data['amount'],
            payment_date=self.cleaned_data['payment_date'],
            payment_method=self.cleaned_data['payment_method'],
            reference_number=self.cleaned_data.get('reference_number', ''),
            notes=self.cleaned_data.get('notes', '')
        )
    
    def _setup_period_choices(self):
        from ..services.period_service import ServicePeriodManager
        pending_periods = ServicePeriodManager.get_pending_periods(self.client_service)
        if not pending_periods.exists():
            self.fields['period'].queryset = ServicePayment.objects.none()
            self.fields['period'].help_text = (
                "No hay períodos pendientes de pago. "
                "Primero debe extender el servicio para crear un período."
            )
            for field in self.fields.values():
                field.disabled = True
        else:
            self.fields['period'].queryset = pending_periods
            period_choices = []
            for period in pending_periods:
                choice_text = (
                    f"{period.period_start} - {period.period_end} "
                    f"({period.duration_days} días) - {period.get_status_display()}"
                )
                period_choices.append((period.id, choice_text))
            self.fields['period'].choices = period_choices
    
    def _setup_dynamic_amount(self):
        if not self.client_service:
            return
        self.fields['period'].widget.attrs.update({
            'data-service-id': self.client_service.id,
            'onchange': 'updateSuggestedAmount(this)'
        })
        self.fields['amount'].widget.attrs.update({
            'data-suggested-amounts': self._get_suggested_amounts_json()
        })
    
    def _get_suggested_amounts_json(self):
        import json
        from ..services.period_service import ServicePeriodManager
        pending_periods = ServicePeriodManager.get_pending_periods(self.client_service)
        suggested_amounts = {}
        for period in pending_periods:
            suggested = PaymentService.calculate_suggested_amount(period, self.client_service)
            if suggested:
                suggested_amounts[str(period.id)] = float(suggested)
        return json.dumps(suggested_amounts)


class BulkPaymentForm(BaseServiceForm, PaymentFieldsMixin):
    
    selected_periods = forms.ModelMultipleChoiceField(
        queryset=ServicePayment.objects.none(),
        required=True,
        label="Períodos a pagar"
    )
    
    apply_same_payment_info = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Aplicar la misma información de pago a todos los períodos",
        help_text="Si está marcado, todos los períodos tendrán la misma fecha y método de pago"
    )
    
    def __init__(self, client_service=None, *args, **kwargs):
        super().__init__(client_service=client_service, *args, **kwargs)
        self.add_payment_fields()
        if self.client_service:
            from ..services.period_service import ServicePeriodManager
            pending_periods = ServicePeriodManager.get_pending_periods(self.client_service)
            self.fields['selected_periods'].queryset = pending_periods
    
    def clean(self):
        cleaned_data = super().clean()
        self.clean_payment_fields()
        periods = cleaned_data.get('selected_periods')
        if not periods:
            raise ValidationError({'selected_periods': 'Debe seleccionar al menos un período'})
        for period in periods:
            if not period.can_be_paid:
                raise ValidationError({
                    'selected_periods': f'El período {period.period_start} - {period.period_end} no puede recibir pagos'
                })
        return cleaned_data
    
    def save(self):
        periods = self.cleaned_data['selected_periods']
        payment_info = {
            'payment_date': self.cleaned_data['payment_date'],
            'payment_method': self.cleaned_data['payment_method'],
            'reference_number': self.cleaned_data.get('reference_number', ''),
            'notes': self.cleaned_data.get('notes', '')
        }
        updated_periods = []
        for period in periods:
            suggested_amount = PaymentService.calculate_suggested_amount(period, self.client_service)
            amount = suggested_amount or self.cleaned_data['amount']
            updated_period = PaymentService.process_payment(
                period=period,
                amount=amount,
                **payment_info
            )
            updated_periods.append(updated_period)
        return updated_periods
