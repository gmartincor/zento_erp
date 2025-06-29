from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .base_forms import BaseServiceForm, PaymentFieldsMixin, RemanenteFieldsMixin
from ..services.payment_service import PaymentService
from ..models import ServicePayment


class PaymentForm(BaseServiceForm, PaymentFieldsMixin, RemanenteFieldsMixin):
    
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
        self.add_remanente_fields()  # Agregar campos de remanentes
        
        if 'amount' in self.fields:
            self.fields['amount'].required = False
            self.fields['amount'].widget = forms.HiddenInput()
        
        if self.client_service:
            from ..services.period_service import ServicePeriodManager
            pending_periods = ServicePeriodManager.get_pending_periods(self.client_service)
            self.fields['selected_periods'].queryset = pending_periods
            
        self._add_widget_classes()
    
    def _add_widget_classes(self):
        base_class = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        
        self.fields['selected_periods'].widget.attrs.update({
            'class': 'text-primary-600 focus:ring-primary-500 border-gray-300 rounded'
        })
        
        if 'apply_same_payment_info' in self.fields:
            self.fields['apply_same_payment_info'].widget.attrs.update({
                'class': 'form-check-input text-primary-600 focus:ring-primary-500 border-gray-300 rounded'
            })

        if 'payment_method' in self.fields:
            self.fields['payment_method'].widget.attrs['class'] = base_class
        if 'payment_date' in self.fields:
            self.fields['payment_date'].widget.attrs['class'] = base_class
        if 'reference_number' in self.fields:
            self.fields['reference_number'].widget.attrs['class'] = base_class
        if 'notes' in self.fields:
            self.fields['notes'].widget.attrs['class'] = base_class
            self.fields['notes'].widget.attrs['placeholder'] = 'Añade cualquier nota relevante sobre este pago...'
    
    def clean(self):
        cleaned_data = super().clean()
        
        periods = cleaned_data.get('selected_periods')
        if not periods:
            raise ValidationError({'selected_periods': 'Debe seleccionar al menos un período'})
        for period in periods:
            if not period.can_be_paid:
                raise ValidationError({
                    'selected_periods': f'El período {period.period_start} - {period.period_end} no puede recibir pagos'
                })
        
        payment_date = cleaned_data.get('payment_date')
        if payment_date and payment_date > timezone.now().date():
            raise ValidationError({
                'payment_date': 'La fecha de pago no puede ser futura'
            })
        
        # Validar campos de remanentes
        self.clean_remanente_fields()
            
        return cleaned_data
    
    def save(self, user=None):
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
            
            if suggested_amount is None or suggested_amount <= 0:
                if hasattr(period, 'amount') and period.amount and period.amount > 0:
                    amount = period.amount
                else:
                    amount = self.client_service.price if self.client_service.price and self.client_service.price > 0 else 0
            else:
                amount = suggested_amount
            
            if amount <= 0:
                raise ValidationError(f'No se pudo determinar un monto válido para el período {period.period_start} - {period.period_end}')
            
            updated_period = PaymentService.process_payment(
                period=period,
                amount=amount,
                **payment_info
            )
            updated_periods.append(updated_period)
        
        # Guardar remanentes si están configurados y hay un usuario válido
        if user:
            remanentes_created = self.save_remanentes(user)
            if remanentes_created:
                # Opcional: agregar información sobre remanentes creados al contexto de respuesta
                for period in updated_periods:
                    if hasattr(period, '_remanentes_created'):
                        period._remanentes_created = remanentes_created
                    else:
                        period._remanentes_created = []
                        
        return updated_periods
