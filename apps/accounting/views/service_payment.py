from django.shortcuts import get_object_or_404, redirect
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse

from ..models import ClientService
from ..forms.payment_form import ServicePaymentForm
from ..forms.renewal_form import ServiceActionForm
from ..services.payment_service import PaymentService
from ..services.service_renewal_service import ServiceRenewalService
from ..services.context_builder import RenewalViewContextMixin
from apps.core.mixins import BusinessLinePermissionMixin


class ServicePaymentView(LoginRequiredMixin, BusinessLinePermissionMixin, FormView):
    template_name = 'accounting/service_payment.html'
    form_class = ServicePaymentForm
    
    def dispatch(self, request, *args, **kwargs):
        self.service = get_object_or_404(ClientService, id=kwargs['service_id'])
        self.check_business_line_permission(self.service.business_line)
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['service'] = self.service
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'service': self.service,
            'page_title': f'Registrar Pago - {self.service.client.full_name}',
            'back_url': reverse('accounting:category-services', kwargs={
                'line_path': self.service.get_line_path(),
                'category': self.service.category
            })
        })
        return context
    
    def form_valid(self, form):
        try:
            payment = PaymentService.create_payment_and_extend_service(
                client_service=self.service,
                amount=form.cleaned_data['amount'],
                payment_method=form.cleaned_data['payment_method'],
                payment_date=form.cleaned_data['payment_date'],
                reference_number=form.cleaned_data['reference_number'],
                notes=form.cleaned_data['notes'],
                extend_months=form.cleaned_data['extend_months']
            )
            
            messages.success(
                self.request,
                f'Pago registrado exitosamente. Servicio activo hasta {payment.period_end.strftime("%d/%m/%Y")}.'
            )
            
            return redirect('accounting:category-services', 
                          line_path=self.service.get_line_path(),
                          category=self.service.category)
        
        except Exception as e:
            messages.error(self.request, f'Error al registrar el pago: {str(e)}')
            return self.form_invalid(form)


class ServiceRenewalView(LoginRequiredMixin, BusinessLinePermissionMixin, RenewalViewContextMixin, FormView):
    template_name = 'accounting/service_renewal.html'
    form_class = ServiceActionForm
    
    def dispatch(self, request, *args, **kwargs):
        self.service = get_object_or_404(ClientService, id=kwargs['service_id'])
        self.check_business_line_permission(self.service.business_line)
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['service'] = self.service
        return kwargs
    
    def get_back_url_kwargs(self):
        return {
            'line_path': self.service.get_line_path(),
            'category': self.service.category
        }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        renewal_context = self.get_renewal_context_data()
        context.update(renewal_context)
        
        return context
    
    def form_valid(self, form):
        action_type = form.cleaned_data['action_type']
        
        try:
            if action_type == 'extend':
                return self._handle_extend_service(form)
            elif action_type == 'renew':
                return self._handle_renew_service(form)
            elif action_type == 'no_renew':
                return self._handle_no_renew(form)
            
        except Exception as e:
            messages.error(self.request, f'Error al procesar la acción: {str(e)}')
            return self.form_invalid(form)
    
    def _handle_extend_service(self, form):
        payment_date = None
        payment_method = None
        reference_number = None
        
        if form.cleaned_data['payment_now']:
            payment_date = form.cleaned_data['payment_date']
            payment_method = form.cleaned_data['payment_method']
            reference_number = form.cleaned_data['reference_number']
        else:
            messages.error(self.request, 'Para extender un servicio, debe registrar el pago.')
            return self.form_invalid(form)
        
        payment = ServiceRenewalService.extend_current_service(
            service=self.service,
            amount=form.cleaned_data['amount'],
            payment_method=payment_method,
            duration_months=form.cleaned_data['duration_months'],
            payment_date=payment_date,
            reference_number=reference_number,
            notes=form.cleaned_data['notes']
        )
        
        messages.success(
            self.request,
            f'Servicio extendido exitosamente. Activo hasta {payment.period_end.strftime("%d/%m/%Y")}.'
        )
        
        return redirect('accounting:category-services', 
                      line_path=self.service.get_line_path(),
                      category=self.service.category)
    
    def _handle_renew_service(self, form):
        payment_date = None
        payment_method = None
        reference_number = None
        
        if form.cleaned_data['payment_now']:
            payment_date = form.cleaned_data['payment_date']
            payment_method = form.cleaned_data['payment_method']
            reference_number = form.cleaned_data['reference_number']
        
        new_service, payment = ServiceRenewalService.create_manual_renewal(
            original_service=self.service,
            start_date=form.cleaned_data['start_date'],
            duration_months=form.cleaned_data['duration_months'],
            amount=form.cleaned_data['amount'],
            payment_date=payment_date,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=form.cleaned_data['notes']
        )
        
        if payment:
            messages.success(
                self.request,
                f'Nuevo servicio creado exitosamente con pago. Activo hasta {payment.period_end.strftime("%d/%m/%Y")}.'
            )
        else:
            messages.success(
                self.request,
                f'Nuevo servicio creado exitosamente. Pendiente de pago desde {new_service.start_date.strftime("%d/%m/%Y")}.'
            )
        
        return redirect('accounting:category-services', 
                      line_path=new_service.get_line_path(),
                      category=new_service.category)
    
    def _handle_no_renew(self, form):
        ServiceRenewalService.mark_service_as_not_renewed(
            service=self.service,
            reason=form.cleaned_data['no_renew_reason']
        )
        
        messages.info(
            self.request,
            f'Servicio marcado como no renovado. El cliente {self.service.client.full_name} decidió no continuar.'
        )
        
        return redirect('accounting:category-services', 
                      line_path=self.service.get_line_path(),
                      category=self.service.category)
