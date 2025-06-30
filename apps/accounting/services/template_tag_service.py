from typing import Dict, Any, Optional
from django.urls import reverse
from apps.accounting.models import ClientService
from apps.core.constants import CATEGORY_DEFAULTS


class TemplateTagService:
    
    @staticmethod
    def get_client_reactivation_status(client) -> Dict[str, Any]:
        from .client_reactivation_service import ClientReactivationService
        return ClientReactivationService.get_client_status(client)
    
    @staticmethod
    def should_show_reactivation_option(client) -> bool:
        from .client_reactivation_service import ClientReactivationService
        status = ClientReactivationService.get_client_status(client)
        return status['status'] in ['long_inactive', 'recently_inactive']
    
    @staticmethod
    def build_reactivation_url(service: ClientService, business_line=None, category=None) -> str:
        if not business_line:
            business_line = service.business_line
        if not category:
            category = service.category
        
        line_path = business_line.get_line_path() if hasattr(business_line, 'get_line_path') else business_line.slug
        return reverse('accounting:service-create', kwargs={
            'line_path': line_path,
            'category': category.lower()
        }) + f'?renew_from={service.id}'
    
    @staticmethod
    def normalize_category(category: str) -> str:
        return category.lower() if category else CATEGORY_DEFAULTS['DEFAULT_CATEGORY']
    
    @staticmethod
    def calculate_percentage(part: float, total: float) -> float:
        if not total or total == 0:
            return 0
        try:
            return (float(part) / float(total)) * 100
        except (ValueError, TypeError, ZeroDivisionError):
            return 0
    
    @staticmethod
    def get_payment_method_icon(method: str) -> str:
        icons = {
            'CARD': '💳',
            'CASH': '💵',
            'TRANSFER': '🏦',
            'BIZUM': '📱'
        }
        return icons.get(method, '💰')
    
    @staticmethod
    def calculate_remanente_total(service: ClientService) -> float:
        if hasattr(service, 'get_remanente_total'):
            return service.get_remanente_total()
        return 0
    
    @staticmethod
    def build_service_edit_url(service: ClientService) -> str:
        """Construye la URL de edición usando los datos reales del servicio"""
        line_path = service.get_line_path()
        category = service.category.lower()
        
        return reverse('accounting:service-edit', kwargs={
            'line_path': line_path,
            'category': category,
            'service_id': service.id
        })
    
    @staticmethod
    def build_service_termination_url(service: ClientService) -> str:
        """Construye la URL de finalización usando los datos reales del servicio"""
        return reverse('accounting:service-terminate', kwargs={
            'service_id': service.id
        })
