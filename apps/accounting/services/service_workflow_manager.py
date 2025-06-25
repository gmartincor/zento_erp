from typing import Dict, Any, Optional, Tuple
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.accounting.models import ClientService, ServicePayment
from apps.accounting.services.client_service_transaction import ClientServiceTransactionManager
from apps.accounting.services.payment_service import PaymentService


class ServiceWorkflowManager:
    
    @staticmethod
    def handle_service_creation_flow(request, form_data: Dict[str, Any], business_line, category) -> Tuple[ClientService, str]:
        with transaction.atomic():
            service = ClientServiceTransactionManager.create_client_service(
                form_data, business_line, category
            )
            
            messages.success(
                request,
                f'Servicio creado exitosamente para {service.client.full_name}. '
                'Ahora puedes configurar el primer pago.'
            )
            
            redirect_url = reverse('accounting:payment-create', kwargs={'service_id': service.id})
            return service, redirect_url
    
    @staticmethod
    def handle_service_update_flow(request, service_instance: ClientService, form_data: Dict[str, Any]) -> Tuple[ClientService, str]:
        with transaction.atomic():
            updated_service = ClientServiceTransactionManager.update_client_service(
                service_instance, form_data
            )
            
            messages.success(
                request,
                f'Servicio actualizado exitosamente para {updated_service.client.full_name}.'
            )
            
            line_path = updated_service.get_line_path()
            category = updated_service.category.lower()
            
            redirect_url = reverse('accounting:category-services', kwargs={
                'line_path': line_path,
                'category': category
            })
            
            return updated_service, redirect_url
    
    @staticmethod
    def handle_payment_creation_flow(request, service_id: int, form_data: Dict[str, Any]) -> Tuple[ServicePayment, str]:
        service = ClientService.objects.get(id=service_id)
        
        with transaction.atomic():
            payment = PaymentService.create_payment(
                client_service=service,
                amount=form_data['amount'],
                period_start=form_data['period_start'],
                period_end=form_data['period_end'],
                payment_method=form_data['payment_method'],
                payment_date=form_data.get('payment_date'),
                reference_number=form_data.get('reference_number', ''),
                notes=form_data.get('notes', ''),
                mark_as_paid=form_data.get('mark_as_paid', True)
            )
            
            if payment.status == ServicePayment.StatusChoices.PAID:
                service.status = ClientService.StatusChoices.ACTIVE
                service.save()
            
            messages.success(
                request,
                f'Pago registrado exitosamente. Servicio activado hasta {payment.period_end.strftime("%d/%m/%Y")}.'
            )
            
            redirect_url = reverse('accounting:service-payment-history', kwargs={'service_id': service.id})
            return payment, redirect_url
    
    @staticmethod
    def validate_service_creation_permissions(user, business_line) -> bool:
        from apps.accounting.services.business_line_service import BusinessLineService
        business_line_service = BusinessLineService()
        accessible_lines = business_line_service.get_accessible_lines(user)
        return business_line in accessible_lines
    
    @staticmethod
    def get_service_next_steps_context(service: ClientService) -> Dict[str, Any]:
        has_payments = service.payments.exists()
        is_active = service.status == ClientService.StatusChoices.ACTIVE
        
        context = {
            'service': service,
            'has_payments': has_payments,
            'is_active': is_active,
            'needs_payment': not has_payments or not is_active,
            'payment_create_url': reverse('accounting:payment-create', kwargs={'service_id': service.id}),
            'payment_history_url': reverse('accounting:service-payment-history', kwargs={'service_id': service.id})
        }
        
        if not has_payments:
            context['next_step_message'] = 'Para activar el servicio, registra el primer pago.'
        elif not is_active:
            context['next_step_message'] = 'El servicio necesita un pago para reactivarse.'
        else:
            context['next_step_message'] = 'Servicio activo. Puedes gestionar pagos adicionales.'
        
        return context
