from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import View
from django.db import transaction

from apps.accounting.models import ServicePayment
from apps.accounting.forms import RefundForm
from apps.core.mixins import BusinessLinePermissionMixin


class PaymentRefundView(LoginRequiredMixin, BusinessLinePermissionMixin, View):
    template_name = 'accounting/payments/refund_form.html'
    
    def get(self, request, payment_id):
        payment = get_object_or_404(ServicePayment, 
                                   id=payment_id,
                                   client_service__business_line__in=self.get_allowed_business_lines())
        
        if payment.status != ServicePayment.StatusChoices.PAID:
            messages.error(request, 'Solo se pueden reembolsar pagos en estado PAGADO')
            return redirect('accounting:payment_detail', payment_id=payment.id)
        
        form = RefundForm(payment=payment)
        return render(request, self.template_name, {
            'form': form,
            'payment': payment
        })
    
    def post(self, request, payment_id):
        payment = get_object_or_404(ServicePayment,
                                   id=payment_id,
                                   client_service__business_line__in=self.get_allowed_business_lines())
        
        if payment.status != ServicePayment.StatusChoices.PAID:
            messages.error(request, 'Solo se pueden reembolsar pagos en estado PAGADO')
            return redirect('accounting:payment_detail', payment_id=payment.id)
        
        form = RefundForm(payment=payment, data=request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    payment.refund(
                        refund_amount=form.cleaned_data['refund_amount'],
                        reason=form.cleaned_data['reason']
                    )
                    messages.success(request, f'Reembolso procesado: ${form.cleaned_data["refund_amount"]}')
                    return redirect('accounting:payment_detail', payment_id=payment.id)
            except Exception as e:
                messages.error(request, f'Error al procesar reembolso: {str(e)}')
        
        return render(request, self.template_name, {
            'form': form,
            'payment': payment
        })
