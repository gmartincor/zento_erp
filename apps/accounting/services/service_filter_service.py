from typing import Dict, List, Optional
from django.db.models import QuerySet
from ..models import ClientService


class ServiceFilterService:
    
    @classmethod
    def apply_filters(cls, queryset: QuerySet, filters: Dict[str, str]) -> QuerySet:
        if filters.get('client'):
            queryset = queryset.filter(client__full_name__icontains=filters['client'])
        
        if filters.get('operational_status'):
            queryset = queryset.with_operational_status(filters['operational_status'])
        
        if filters.get('payment_status'):
            queryset = queryset.with_payment_status(filters['payment_status'])
        
        if filters.get('renewal_status'):
            queryset = queryset.with_renewal_status(filters['renewal_status'])
        
        if filters.get('status'):
            queryset = queryset.with_status(filters['status'])
        
        return queryset
    
    @classmethod
    def get_filter_summary(cls, filters: Dict[str, str]) -> Dict[str, str]:
        summary = {}
        
        if filters.get('client'):
            summary['Cliente'] = f"Contiene '{filters['client']}'"
        
        if filters.get('operational_status'):
            operational_labels = {
                'active': 'Activos',
                'inactive': 'Inactivos',
                'suspended': 'Suspendidos'
            }
            summary['Estado Operacional'] = operational_labels.get(
                filters['operational_status'], 
                filters['operational_status']
            )
        
        if filters.get('payment_status'):
            payment_labels = {
                'AWAITING_START': 'Periodo creado sin pago',
                'UNPAID_ACTIVE': 'Pendiente de pago', 
                'PAID': 'Pagado',
                'OVERDUE': 'Vencido',
                'REFUNDED': 'Reembolsado',
                'no_payments': 'Sin pagos'
            }
            summary['Estado de Pagos'] = payment_labels.get(
                filters['payment_status'], 
                filters['payment_status']
            )
        
        if filters.get('renewal_status'):
            renewal_labels = {
                'active': 'Al día',
                'no_periods': 'Sin períodos',
                'renewal_pending': 'Pendiente de renovación',
                'expiring_soon': 'Vence pronto',
                'expired': 'Vencido',
                'inactive': 'Pausado',
                'suspended': 'Suspendido'
            }
            summary['Estado de Renovación'] = renewal_labels.get(
                filters['renewal_status'], 
                filters['renewal_status']
            )
        
        if filters.get('status'):
            legacy_labels = {
                'active': 'Activos',
                'expiring_soon': 'Vencen Pronto',
                'renewal_due': 'Renovar Pronto',
                'expired': 'Vencidos',
                'suspended': 'Suspendidos',
                'inactive': 'Pausados'
            }
            summary['Estado General'] = legacy_labels.get(
                filters['status'], 
                filters['status']
            )
        
        return summary
    
    @classmethod
    def get_active_filters_count(cls, filters: Dict[str, str]) -> int:
        filter_keys = ['client', 'operational_status', 'payment_status', 'renewal_status', 'status']
        return sum(1 for key in filter_keys if filters.get(key))
    
    @classmethod
    def are_filters_compatible(cls, filters: Dict[str, str]) -> bool:
        has_new_filters = any(filters.get(key) for key in 
                             ['operational_status', 'payment_status', 'renewal_status'])
        has_legacy_filter = bool(filters.get('status'))
        
        if has_new_filters and has_legacy_filter:
            return False
        
        return True
    
    @classmethod
    def get_filter_conflicts(cls, filters: Dict[str, str]) -> List[str]:
        conflicts = []
        
        if not cls.are_filters_compatible(filters):
            conflicts.append(
                "No se pueden usar filtros específicos junto con el filtro general. "
                "Use solo filtros específicos o solo el filtro general."
            )
        
        return conflicts
