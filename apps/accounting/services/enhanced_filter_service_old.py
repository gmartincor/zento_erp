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

    
    @classmethod
    def apply_filters(cls, queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        status_filter = filters.get('status')
        operational_status = filters.get('operational_status')
        payment_status = filters.get('payment_status')
        renewal_status = filters.get('renewal_status')
        client_filter = filters.get('client')
        
        if status_filter:
            queryset = queryset.with_status(status_filter)
        
        if operational_status:
            queryset = queryset.with_operational_status(operational_status)
        
        if payment_status:
            queryset = queryset.with_payment_status(payment_status)
        
        if renewal_status:
            queryset = queryset.with_renewal_status(renewal_status)
        
        if client_filter:
            queryset = queryset.filter(client__full_name__icontains=client_filter)
        
        return queryset
    
    @classmethod
    def get_active_filters(cls, request_params: Dict[str, str]) -> Dict[str, Any]:
        active_filters = {}

        if request_params.get('status'):
            active_filters['status'] = {
                'type': 'general',
                'value': request_params['status'],
                'label': cls._get_status_label(request_params['status'])
            }
        
        if request_params.get('operational_status'):
            active_filters['operational_status'] = {
                'type': 'operational',
                'value': request_params['operational_status'],
                'label': cls._get_operational_status_label(request_params['operational_status'])
            }
        
        if request_params.get('payment_status'):
            active_filters['payment_status'] = {
                'type': 'payment',
                'value': request_params['payment_status'],
                'label': cls._get_payment_status_label(request_params['payment_status'])
            }
        
        if request_params.get('renewal_status'):
            active_filters['renewal_status'] = {
                'type': 'renewal',
                'value': request_params['renewal_status'],
                'label': cls._get_renewal_status_label(request_params['renewal_status'])
            }
        
        if request_params.get('client'):
            active_filters['client'] = {
                'type': 'search',
                'value': request_params['client'],
                'label': f'Cliente: "{request_params["client"]}"'
            }
        
        return active_filters
    
    @classmethod
    def detect_conflicts(cls, request_params: Dict[str, str]) -> List[str]:
        conflicts = []
        
        if request_params.get('status') and (
            request_params.get('operational_status') or
            request_params.get('payment_status') or 
            request_params.get('renewal_status')
        ):
            conflicts.append(
                'Se está usando tanto el filtro general como filtros específicos. '
                'Los filtros específicos pueden sobrescribir el comportamiento del filtro general.'
            )
        
        # Conflictos específicos de renovación
        general_status = request_params.get('status')
        renewal_status = request_params.get('renewal_status')
        
        if general_status and renewal_status:
            conflicting_combinations = [
                ('active', 'expiring_soon'),
                ('active', 'renewal_due'),
                ('expired', 'active_long_term'),
                ('expiring_soon', 'active_long_term'),
                ('renewal_due', 'expired')
            ]
            
            if (general_status, renewal_status) in conflicting_combinations:
                conflicts.append(
                    f'El filtro general "{general_status}" puede no ser compatible '
                    f'con el filtro de renovación "{renewal_status}".'
                )
        
        return conflicts
    
    @classmethod
    def _get_status_label(cls, status: str) -> str:
        labels = {
            'active': 'Al día (>30 días)',
            'renewal_due': 'Pendiente renovación (7-30 días)',
            'expiring_soon': 'Vence pronto (<7 días)',
            'expired': 'Vencido',
            'suspended': 'Suspendido',
            'inactive': 'Inactivo'
        }
        return labels.get(status, status.title())
    
    @classmethod
    def _get_operational_status_label(cls, status: str) -> str:
        labels = {
            'active': 'Operacional activo',
            'suspended': 'Operacional suspendido',
            'inactive': 'Operacional inactivo'
        }
        return labels.get(status, status.title())
    
    @classmethod
    def _get_payment_status_label(cls, status: str) -> str:
        labels = {
            'up_to_date': 'Pagos al día',
            'pending_payment': 'Pago pendiente',
            'overdue_payment': 'Pago vencido',
            'no_payments': 'Sin pagos'
        }
        return labels.get(status, status.title())
    
    @classmethod
    def _get_renewal_status_label(cls, status: str) -> str:
        labels = {
            'active_long_term': 'Largo plazo (>30 días)',
            'renewal_due': 'Renovar pronto (7-30 días)', 
            'expiring_soon': 'Vence pronto (<7 días)',
            'expired': 'Vencido'
        }
        return labels.get(status, status.title())
