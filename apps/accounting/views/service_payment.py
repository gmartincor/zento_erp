from django.shortcuts import get_object_or_404, redirect
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse

from ..models import ClientService
from ..forms.payment_form import ServicePaymentForm
from ..forms.renewal_form import ServiceActionForm
from ..services.payment_service import PaymentService
from ..services.service_manager import ServiceManager
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


class ServiceRenewalView(LoginRequiredMixin, BusinessLinePermissionMixin, FormView):
    template_name = 'accounting/service_renewal.html'
    form_class = ServiceActionForm
    
    def dispatch(self, request, *args, **kwargs):
        self.service = get_object_or_404(ClientService, id=kwargs['service_id'])
        self.check_business_line_permission(self.service.business_line)
        return super().dispatch(request, *args, **kwargs)
    
    def _refresh_service(self):
        self.service.get_fresh_service_data()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self._refresh_service()
        kwargs['service'] = self.service
        return kwargs
    
    def get_back_url_kwargs(self):
        return {
            'line_path': self.service.get_line_path(),
            'category': self.service.category
        }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        self._refresh_service()
        
        context.update({
            'service': self.service,
            'page_title': f'Gestionar Servicio - {self.service.client.full_name}',
            'back_url': reverse('accounting:category-services', kwargs={
                'line_path': self.service.get_line_path(),
                'category': self.service.category
            })
        })
        
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
        try:
            if form.cleaned_data['payment_now']:
                payment = PaymentService.create_payment_and_extend_service(
                    client_service=self.service,
                    amount=form.cleaned_data['amount'],
                    payment_method=form.cleaned_data['payment_method'],
                    payment_date=form.cleaned_data['payment_date'],
                    reference_number=form.cleaned_data.get('reference_number'),
                    notes=form.cleaned_data.get('notes'),
                    extend_months=form.cleaned_data['duration_months']
                )
                messages.success(
                    self.request,
                    f'Servicio extendido con pago. Activo hasta {payment.period_end.strftime("%d/%m/%Y")}.'
                )
            else:
                ServiceManager.extend_service_without_payment(
                    service=self.service,
                    extension_months=form.cleaned_data['duration_months'],
                    notes=form.cleaned_data.get('notes')
                )
                messages.success(
                    self.request,
                    f'Servicio extendido sin pago por {form.cleaned_data["duration_months"]} meses.'
                )
        except Exception as e:
            messages.error(self.request, f'Error al extender el servicio: {str(e)}')
            return self.form_invalid(form)
        
        return redirect('accounting:category-services', 
                      line_path=self.service.get_line_path(),
                      category=self.service.category)
    
    def _handle_renew_service(self, form):
        messages.info(
            self.request,
            'La creación de nuevos servicios se ha simplificado. Use la opción "Crear Servicio" en lugar de renovar.'
        )
        
        return redirect('accounting:service-create', 
                      line_path=self.service.get_line_path(),
                      category=self.service.category)
    
    def _handle_no_renew(self, form):
        self.service.status = self.service.StatusChoices.INACTIVE
        
        reason = form.cleaned_data.get('no_renew_reason', '')
        if reason:
            existing_notes = self.service.notes or ""
            self.service.notes = f"{existing_notes}\nNo renovado: {reason}".strip()
        
        self.service.save()
        
        messages.info(
            self.request,
            f'Servicio marcado como no renovado. El cliente {self.service.client.full_name} decidió no continuar.'
        )
        
        return redirect('accounting:category-services', 
                      line_path=self.service.get_line_path(),
                      category=self.service.category)
