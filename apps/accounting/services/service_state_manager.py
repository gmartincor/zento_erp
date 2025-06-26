from typing import Dict, Any, Optional
from datetime import date, timedelta
from django.utils import timezone
from ..models import ClientService, ServicePayment
from .date_calculator import DateCalculator


class ServiceStateManager:
    
    RENEWAL_WARNING_DAYS = 30
    EXPIRING_SOON_DAYS = 7
    
    @classmethod
    def is_service_active(cls, service) -> bool:
        if not service.is_active:
            return False
        
        if service.admin_status == 'DISABLED':
            return False
        
        active_until = service.end_date
        if not active_until:
            return service.is_active
        
        return not DateCalculator.is_date_in_past(active_until)
    
    @classmethod
    def is_service_expired(cls, service: ClientService) -> bool:
        if not service.is_active:
            return True
            
        active_until = service.end_date
        if not active_until:
            return False
            
        return DateCalculator.is_date_in_past(active_until)
    
    @classmethod
    def days_until_expiry(cls, service: ClientService) -> int:
        active_until = service.end_date
        if not active_until:
            return 0
        
        return DateCalculator.days_between(DateCalculator.get_today(), active_until)
    
    @classmethod
    def needs_renewal(cls, service: ClientService) -> bool:
        if not service.is_active:
            return True
        
        if cls.is_service_expired(service):
            return True
        
        days_until_expiry = cls.days_until_expiry(service)
        return days_until_expiry <= cls.RENEWAL_WARNING_DAYS
    
    @classmethod
    def get_service_status(cls, service) -> str:
        if not service.is_active:
            return 'inactive'
        
        if service.admin_status == 'DISABLED':
            return 'disabled'
        
        if cls.is_service_expired(service):
            return 'expired'
        
        days_left = cls.days_until_expiry(service)
        if days_left <= cls.EXPIRING_SOON_DAYS:
            return 'expiring_soon'
        elif days_left <= cls.RENEWAL_WARNING_DAYS:
            return 'renewal_due'
        else:
            return 'active'
    
    @classmethod
    def get_status_display_data(cls, service: ClientService) -> Dict[str, Any]:
        status = cls.get_service_status(service)
        days_left = cls.days_until_expiry(service)
        active_until = service.end_date
        
        status_map = {
            'active': {
                'label': 'Activo',
                'class': 'badge-success',
                'icon': 'check-circle',
                'color': 'green'
            },
            'renewal_due': {
                'label': f'Renovar en {days_left} días' if days_left > 0 else 'Renovar pronto',
                'class': 'badge-warning',
                'icon': 'exclamation-triangle',
                'color': 'yellow'
            },
            'expiring_soon': {
                'label': cls._get_expiring_label(days_left),
                'class': 'badge-danger',
                'icon': 'clock',
                'color': 'orange'
            },
            'expired': {
                'label': cls._get_expired_label(days_left),
                'class': 'badge-danger',
                'icon': 'x-circle',
                'color': 'red'
            },
            'inactive': {
                'label': 'Inactivo',
                'class': 'badge-secondary',
                'icon': 'pause-circle',
                'color': 'gray'
            },
            'disabled': {
                'label': 'Deshabilitado',
                'class': 'badge-dark',
                'icon': 'ban',
                'color': 'black'
            }
        }
        
        base_data = status_map.get(status, status_map['inactive'])
        base_data.update({
            'status': status,
            'days_left': days_left,
            'active_until': active_until
        })
        
        return base_data
    
    @classmethod
    def _get_expiring_label(cls, days_left: int) -> str:
        if days_left == 0:
            return 'Vence hoy'
        elif days_left == 1:
            return 'Vence mañana'
        elif days_left > 0:
            return f'Vence en {days_left} días'
        else:
            return cls._get_expired_label(days_left)
    
    @classmethod
    def _get_expired_label(cls, days_left: int) -> str:
        if days_left == 0:
            return 'Vence hoy'
        elif days_left < 0:
            return f'Vencido {DateCalculator.format_days_difference(days_left)}'
        else:
            return 'Vencido'
    
    @classmethod
    def get_status_display(cls, status: str) -> str:
        status_labels = {
            'active': 'Activo',
            'renewal_due': 'Renovar Pronto',
            'expiring_soon': 'Vence Pronto',
            'expired': 'Vencido',
            'inactive': 'Inactivo',
            'disabled': 'Deshabilitado'
        }
        return status_labels.get(status, 'Desconocido')
    
    @classmethod
    def get_status_priority(cls, status: str) -> int:
        priorities = {
            'expired': 1,
            'expiring_soon': 2,
            'renewal_due': 3,
            'disabled': 4,
            'inactive': 5,
            'active': 6,
        }
        return priorities.get(status, 0)
    
    @classmethod
    def get_service_summary(cls, service: ClientService) -> Dict[str, Any]:
        status = cls.get_service_status(service)
        days_left = cls.days_until_expiry(service)
        active_until = service.end_date
        
        return {
            'status': status,
            'status_display': cls.get_status_display(status),
            'is_active': cls.is_service_active(service),
            'is_expired': cls.is_service_expired(service),
            'needs_renewal': cls.needs_renewal(service),
            'days_left': days_left,
            'active_until': active_until,
            'priority': cls.get_status_priority(status)
        }
