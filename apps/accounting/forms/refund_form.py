from django import forms
from django.core.exceptions import ValidationError
from ..models import ServicePayment


class RefundForm(forms.Form):
    refund_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label="Monto a reembolsar",
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
        self.fields['refund_amount'].widget.attrs.update({
            'max': str(payment.amount - (payment.refunded_amount or 0)),
            'step': '0.01',
            'placeholder': f'Máximo: {payment.amount - (payment.refunded_amount or 0)}'
        })
    
    def clean_refund_amount(self):
        refund_amount = self.cleaned_data.get('refund_amount')
        if refund_amount is None:
            return self.payment.amount - (self.payment.refunded_amount or 0)
        
        max_refund = self.payment.amount - (self.payment.refunded_amount or 0)
        if refund_amount > max_refund:
            raise ValidationError(f'El monto máximo a reembolsar es {max_refund}')
        
        if refund_amount <= 0:
            raise ValidationError('El monto debe ser mayor a 0')
        
        return refund_amount
