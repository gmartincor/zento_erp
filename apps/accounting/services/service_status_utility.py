from typing import Dict, List, Any, QuerySet
from django.db.models import Count, Q
from ..models import ClientService
from .service_state_manager import ServiceStateManager


class ServiceStatusUtility:
    
    @classmethod
    def get_services_by_status(cls, status: str, business_lines: QuerySet = None) -> QuerySet:
        queryset = ClientService.services.all()
        if business_lines:
            queryset = queryset.filter(business_line__in=business_lines)
        return queryset.with_status(status)
    
    @classmethod
    def get_status_counts(cls, business_lines: QuerySet = None) -> Dict[str, int]:
        base_queryset = ClientService.services.all()
        if business_lines:
            base_queryset = base_queryset.filter(business_line__in=business_lines)
        
        return {
            'active': base_queryset.with_status('active').count(),
            'expiring_soon': base_queryset.with_status('expiring_soon').count(),
            'renewal_due': base_queryset.with_status('renewal_due').count(),
            'expired': base_queryset.with_status('expired').count(),
            'disabled': base_queryset.with_status('disabled').count(),
            'inactive': base_queryset.with_status('inactive').count(),
        }
    
    @classmethod
    def get_services_with_status_data(cls, services: QuerySet) -> List[Dict[str, Any]]:
        result = []
        for service in services:
            status_data = service.status_display_data
            result.append({
                'service': service,
                'status': status_data['status'],
                'status_display': status_data['label'],
                'status_color': status_data['color'],
                'priority': status_data.get('priority', 0)
            })
        
        return sorted(result, key=lambda x: x['priority'])
    
    @classmethod
    def get_critical_services(cls, business_lines: QuerySet = None) -> List[Dict[str, Any]]:
        expired = cls.get_services_by_status('expired', business_lines)
        expiring_soon = cls.get_services_by_status('expiring_soon', business_lines)
        
        critical_services = list(expired) + list(expiring_soon)
        return cls.get_services_with_status_data(critical_services)
