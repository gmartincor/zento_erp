from typing import Dict, List, Optional, Any
from django.db.models import QuerySet
from .service_filter_service import ServiceFilterService
from .status_display_service import StatusDisplayService


class EnhancedFilterService:
    
    @classmethod
    def apply_filters(cls, queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        return ServiceFilterService.apply_filters(queryset, filters)
    
    @classmethod
    def get_active_filters(cls, request_params: Dict[str, str]) -> Dict[str, Any]:
        active_filters = {}
        
        if request_params.get('status'):
            active_filters['status'] = {
                'value': request_params['status'],
                'label': cls._get_legacy_status_label(request_params['status'])
            }
        
        if request_params.get('operational_status'):
            active_filters['operational_status'] = {
                'value': request_params['operational_status'],
                'label': cls._get_operational_status_label(request_params['operational_status'])
            }
        
        if request_params.get('payment_status'):
            if request_params['payment_status'] == 'no_payments':
                label = 'Sin pagos'
            else:
                status_data = StatusDisplayService.get_payment_status_display(request_params['payment_status'])
                label = status_data['label']
            active_filters['payment_status'] = {
                'value': request_params['payment_status'],
                'label': label
            }
        
        if request_params.get('renewal_status'):
            status_data = StatusDisplayService.get_service_status_display(request_params['renewal_status'])
            active_filters['renewal_status'] = {
                'value': request_params['renewal_status'],
                'label': status_data['label']
            }
        
        if request_params.get('client'):
            active_filters['client'] = {
                'value': request_params['client'],
                'label': f"Cliente: {request_params['client']}"
            }
        
        return active_filters
    
    @classmethod
    def get_filter_summary(cls, filters: Dict[str, str]) -> Dict[str, str]:
        return ServiceFilterService.get_filter_summary(filters)
    
    @classmethod
    def get_active_filters_count(cls, filters: Dict[str, str]) -> int:
        return ServiceFilterService.get_active_filters_count(filters)
    
    @classmethod
    def are_filters_compatible(cls, filters: Dict[str, str]) -> bool:
        return ServiceFilterService.are_filters_compatible(filters)
    
    @classmethod
    def get_filter_conflicts(cls, filters: Dict[str, str]) -> List[str]:
        return ServiceFilterService.get_filter_conflicts(filters)
    
    @classmethod
    def detect_conflicts(cls, request_params: Dict[str, str]) -> List[str]:
        return ServiceFilterService.get_filter_conflicts(request_params)
    
    @classmethod
    def _get_legacy_status_label(cls, status: str) -> str:
        labels = {
            'active': 'Activos',
            'expiring_soon': 'Vencen Pronto',
            'renewal_due': 'Renovar Pronto',
            'expired': 'Vencidos',
            'suspended': 'Suspendidos',
            'inactive': 'Pausados'
        }
        if isinstance(status, list):
            return str(status)
        return labels.get(status, str(status))
    
    @classmethod
    def _get_operational_status_label(cls, status: str) -> str:
        labels = {
            'active': 'Activos',
            'suspended': 'Suspendidos',
            'inactive': 'Inactivos'
        }
        if isinstance(status, list):
            return str(status)
        return labels.get(status, str(status))
