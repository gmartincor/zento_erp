from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.core.exceptions import ValidationError

from ..models import ServicePayment
from ..forms.payment_edit_form import PaymentEditForm
from ..services.payment_service import PaymentService
from apps.core.mixins import BusinessLinePermissionMixin


class PaymentEditView(LoginRequiredMixin, BusinessLinePermissionMixin, View):
    template_name = 'accounting/payments/payment_edit.html'
    
    def get_object(self, payment_id):
        payment = get_object_or_404(ServicePayment, id=payment_id)
        
        accessible_lines = self.get_allowed_business_lines()
        if payment.client_service.business_line not in accessible_lines:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("No tiene permisos para editar este pago.")
        
        return payment
    
    def get(self, request, payment_id):
        payment = self.get_object(payment_id)
        form = PaymentEditForm(payment=payment)
        
        context = {
            'form': form,
            'payment': payment,
            'client_service': payment.client_service,
            'client': payment.client_service.client,
            'page_title': 'Editar Pago'
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, payment_id):
        payment = self.get_object(payment_id)
        form = PaymentEditForm(payment=payment, data=request.POST)
        
        if form.is_valid():
            try:
                updated_payment = form.save()
                
                messages.success(
                    request, 
                    f"Pago actualizado exitosamente. Importe neto: €{updated_payment.net_amount}"
                )
                
                return redirect('accounting:payments')
                
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
                else:
                    messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error inesperado: {str(e)}")
        
        context = {
            'form': form,
            'payment': payment,
            'client_service': payment.client_service,
            'client': payment.client_service.client,
            'page_title': 'Editar Pago'
        }
        
        return render(request, self.template_name, context)
