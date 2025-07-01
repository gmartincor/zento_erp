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
    
    def _get_payment(self, payment_id):
        return get_object_or_404(ServicePayment, 
                               id=payment_id,
                               client_service__business_line__in=self.get_allowed_business_lines())
    
    def _validate_payment_status(self, payment):
        return payment.status == ServicePayment.StatusChoices.PAID
    
    def _handle_invalid_payment(self, payment):
        messages.error(self.request, 'Solo se pueden reembolsar pagos en estado PAGADO')
        return redirect('accounting:client-service-detail', service_id=payment.client_service.id)
    
    def _render_form(self, payment, form=None):
        if form is None:
            form = RefundForm(payment=payment)
        return render(self.request, self.template_name, {
            'form': form,
            'payment': payment
        })
    
    def get(self, request, payment_id):
        self.request = request
        payment = self._get_payment(payment_id)
        
        if not self._validate_payment_status(payment):
            return self._handle_invalid_payment(payment)
        
        return self._render_form(payment)
    
    def post(self, request, payment_id):
        self.request = request
        payment = self._get_payment(payment_id)
        
        if not self._validate_payment_status(payment):
            return self._handle_invalid_payment(payment)
        
        form = RefundForm(payment=payment, data=request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    payment.refund(
                        refund_amount=form.cleaned_data['refund_amount'],
                        reason=form.cleaned_data['reason']
                    )
                    messages.success(request, f'Reembolso procesado: €{form.cleaned_data["refund_amount"]}')
                    return redirect('accounting:client-service-detail', service_id=payment.client_service.id)
            except Exception as e:
                messages.error(request, f'Error al procesar reembolso: {str(e)}')
        
        return self._render_form(payment, form)
