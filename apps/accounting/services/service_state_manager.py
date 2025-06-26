from typing import Dict, Any, Optional
from datetime import date, timedelta
from django.utils import timezone
from ..models import ClientService, ServicePayment
from .date_calculator import DateCalculator


class ServiceStateManager:
    
    RENEWAL_WARNING_DAYS = 30
    EXPIRING_SOON_DAYS = 7
    
    @classmethod
    def is_service_active(cls, service: ClientService) -> bool:
        if not service.is_active:
            return False
        
        active_until = cls._get_service_active_until(service)
        if not active_until:
            return service.is_active
        
        return not DateCalculator.is_date_in_past(active_until)
    
    @classmethod
    def is_service_expired(cls, service: ClientService) -> bool:
        if not service.is_active:
            return True
            
        active_until = cls._get_service_active_until(service)
        if not active_until:
            return False
            
        return DateCalculator.is_date_in_past(active_until)
    
    @classmethod
    def days_until_expiry(cls, service: ClientService) -> int:
        active_until = cls._get_service_active_until(service)
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
    def get_service_status(cls, service: ClientService) -> str:
        if not service.is_active:
            return 'inactive'
        
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
        active_until = cls._get_service_active_until(service)
        
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
    def _get_service_active_until(cls, service: ClientService) -> Optional[date]:
        latest_payment = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-period_end').first()
        
        service_end_date = service.end_date
        
        if latest_payment and service_end_date:
            return max(latest_payment.period_end, service_end_date)
        elif latest_payment:
            return latest_payment.period_end
        else:
            return service_end_date
    
    @classmethod
    def get_status_display(cls, status: str) -> str:
        status_labels = {
            'active': 'Activo',
            'renewal_due': 'Renovar Pronto',
            'expiring_soon': 'Vence Pronto',
            'expired': 'Vencido',
            'inactive': 'Inactivo'
        }
        return status_labels.get(status, 'Desconocido')
    
    @classmethod
    def get_status_priority(cls, status: str) -> int:
        priorities = {
            'expired': 1,
            'expiring_soon': 2,
            'renewal_due': 3,
            'inactive': 4,
            'active': 5,
        }
        return priorities.get(status, 0)
    
    @classmethod
    def get_service_summary(cls, service: ClientService) -> Dict[str, Any]:
        status = cls.get_service_status(service)
        days_left = cls.days_until_expiry(service)
        active_until = cls._get_service_active_until(service)
        
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
