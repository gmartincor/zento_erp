from django import forms
from django.core.exceptions import ValidationError
from ..models import ServicePayment


class RefundForm(forms.Form):
    refund_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label="Importe a reembolsar",
        help_text="Deja vacío para reembolso total"
    )
    reason = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label="Motivo del reembolso"
    )
    
    def __init__(self, payment, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.payment = payment
        
        base_class = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        
        self.fields['refund_amount'].widget.attrs.update({
            'class': base_class,
            'type': 'number',
            'max': str(payment.amount - (payment.refunded_amount or 0)),
            'step': '0.01',
            'placeholder': f'Máximo: {payment.amount - (payment.refunded_amount or 0)}'
        })
        
        self.fields['reason'].widget.attrs.update({
            'class': base_class,
            'placeholder': 'Describe el motivo del reembolso...'
        })
    
    def clean_refund_amount(self):
        refund_amount = self.cleaned_data.get('refund_amount')
        if refund_amount is None:
            return self.payment.amount - (self.payment.refunded_amount or 0)
        
        max_refund = self.payment.amount - (self.payment.refunded_amount or 0)
        if refund_amount > max_refund:
            raise ValidationError(f'El importe máximo a reembolsar es {max_refund}')
        
        if refund_amount <= 0:
            raise ValidationError('El importe debe ser mayor a 0')
        
        return refund_amount
