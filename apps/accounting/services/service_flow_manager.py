from typing import Dict, Any, Optional
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.http import Http404

from apps.accounting.models import ClientService
from apps.core.constants import ACCOUNTING_SUCCESS_MESSAGES


class ServiceFlowManager:
    
    @staticmethod
    def validate_service_access(service: ClientService, business_line, category) -> None:
        if service.business_line != business_line:
            raise Http404("Servicio no encontrado en esta línea de negocio.")
        
        if service.category != category:
            raise Http404("Servicio no encontrado en esta categoría.")
    
    @staticmethod
    def get_service_urls(service: ClientService) -> Dict[str, str]:
        line_path = service.get_line_path()
        category = service.category.lower()
        
        return {
            'edit_url': reverse('accounting:service-edit', kwargs={
                'line_path': line_path,
                'category': category,
                'service_id': service.id
            }),
            'category_list_url': reverse('accounting:category-services', kwargs={
                'line_path': line_path,
                'category': category
            }),
            'payment_history_url': reverse('accounting:service-payment-history', kwargs={
                'service_id': service.id
            }),
            'payment_create_url': reverse('accounting:payment-create', kwargs={
                'service_id': service.id
            })
        }
    
    @staticmethod
    def get_navigation_context(line_path: str, category: str) -> Dict[str, str]:
        return {
            'create_url': reverse('accounting:service-create', kwargs={
                'line_path': line_path,
                'category': category.lower()
            }),
            'category_list_url': reverse('accounting:category-services', kwargs={
                'line_path': line_path,
                'category': category.lower()
            }),
            'line_detail_url': reverse('accounting:business-lines-path', kwargs={
                'line_path': line_path
            })
        }
    
    @staticmethod
    def handle_service_creation_success(request, service: ClientService) -> None:
        messages.success(
            request,
            ACCOUNTING_SUCCESS_MESSAGES.get('SERVICE_CREATED', 'Servicio creado correctamente para {client}').format(
                client=service.client.full_name
            )
        )
    
    @staticmethod
    def handle_service_update_success(request, service: ClientService) -> None:
        messages.success(
            request,
            ACCOUNTING_SUCCESS_MESSAGES.get('SERVICE_UPDATED', 'Servicio actualizado correctamente.')
        )


class ServiceContextBuilder:
    
    def __init__(self, service: ClientService):
        self.service = service
    
    def build_base_context(self) -> Dict[str, Any]:
        urls = ServiceFlowManager.get_service_urls(self.service)
        
        return {
            'service': self.service,
            'client': self.service.client,
            'business_line': self.service.business_line,
            'category': self.service.category,
            'category_display': self.service.get_category_display(),
            **urls
        }
    
    def build_edit_context(self) -> Dict[str, Any]:
        context = self.build_base_context()
        context.update({
            'page_title': f'Editar Servicio - {self.service.client.full_name}',
            'back_url': context['category_list_url']
        })
        return context
    
    def build_payment_context(self) -> Dict[str, Any]:
        context = self.build_base_context()
        context.update({
            'page_title': f'Pagos - {self.service.client.full_name}',
            'total_paid': self.service.total_paid,
            'payment_count': self.service.payment_count,
            'current_status': self.service.current_status,
            'active_until': self.service.active_until
        })
        return context
