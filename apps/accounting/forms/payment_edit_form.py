from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .base_forms import BaseServiceForm, PaymentFieldsMixin, RemanenteFieldsMixin
from ..models import ServicePayment


class PaymentEditForm(BaseServiceForm, PaymentFieldsMixin, RemanenteFieldsMixin):
    
    def __init__(self, payment=None, *args, **kwargs):
        self.payment = payment
        client_service = payment.client_service if payment else None
        
        super().__init__(client_service=client_service, *args, **kwargs)
        self.add_payment_fields()
        self.add_remanente_fields()
        
        if self.payment:
            self._populate_initial_data()
        
        self._add_widget_classes()
        self._configure_field_requirements()
    
    def _populate_initial_data(self):
        self.fields['amount'].initial = self.payment.net_amount
        self.fields['payment_date'].initial = self.payment.payment_date
        self.fields['payment_method'].initial = self.payment.payment_method
        self.fields['reference_number'].initial = self.payment.reference_number
        self.fields['notes'].initial = self.payment.notes
        
        if hasattr(self, 'remanente') and self.payment.remanente is not None:
            self.fields['remanente'].initial = self.payment.remanente
    
    def _add_widget_classes(self):
        base_class = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        
        field_mappings = {
            'amount': base_class,
            'payment_method': base_class,
            'payment_date': base_class,
            'reference_number': base_class,
            'notes': base_class,
            'remanente': base_class
        }
        
        for field_name, css_class in field_mappings.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['class'] = css_class
        
        if 'notes' in self.fields:
            self.fields['notes'].widget.attrs['placeholder'] = 'Notas adicionales sobre este pago...'
            self.fields['notes'].widget.attrs['rows'] = '3'
    
    def _configure_field_requirements(self):
        required_fields = ['amount', 'payment_date', 'payment_method']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError('El importe debe ser mayor a cero.')
        return amount
    
    def clean_payment_date(self):
        payment_date = self.cleaned_data.get('payment_date')
        if payment_date and payment_date > timezone.now().date():
            raise ValidationError('La fecha de pago no puede ser futura.')
        return payment_date
    
    def clean_remanente(self):
        remanente = self.cleaned_data.get('remanente')
        if remanente is not None and self.client_service:
            if self.client_service.category != self.client_service.CategoryChoices.BUSINESS:
                raise ValidationError('Los remanentes solo pueden aplicarse a servicios BUSINESS.')
        return remanente
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.payment and self.payment.status != ServicePayment.StatusChoices.PAID:
            raise ValidationError('Solo se pueden editar pagos con estado PAGADO.')
        
        return cleaned_data
    
    def save(self, commit=True):
        if not self.payment:
            raise ValidationError('No se puede guardar sin una instancia de pago.')
        
        new_net_amount = self.cleaned_data['amount']
        current_refunded = self.payment.refunded_amount or 0
        
        self.payment.amount = new_net_amount + current_refunded
        self.payment.payment_date = self.cleaned_data['payment_date']
        self.payment.payment_method = self.cleaned_data['payment_method']
        self.payment.reference_number = self.cleaned_data.get('reference_number', '')
        self.payment.notes = self.cleaned_data.get('notes', '')
        
        if 'remanente' in self.cleaned_data:
            self.payment.remanente = self.cleaned_data.get('remanente')
        
        if commit:
            self.payment.save()
        
        return self.payment
