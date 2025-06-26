from typing import Dict, Any
from datetime import date, timedelta
from django.utils import timezone
from ..models import ClientService, ServicePayment


class ServiceStateManager:
    
    @classmethod
    def is_service_active(cls, service: ClientService) -> bool:
        if not service.is_active:
            return False
        
        active_until = cls._get_service_active_until(service)
        if not active_until:
            return service.is_active
        
        return active_until >= timezone.now().date()
    
    @classmethod
    def is_service_expired(cls, service: ClientService) -> bool:
        return not cls.is_service_active(service)
    
    @classmethod
    def days_until_expiry(cls, service: ClientService) -> int:
        active_until = cls._get_service_active_until(service)
        if not active_until:
            return 0
        
        delta = active_until - timezone.now().date()
        return max(0, delta.days)
    
    @classmethod
    def needs_renewal(cls, service: ClientService) -> bool:
        if not cls.is_service_active(service):
            return True
        
        days_until_expiry = cls.days_until_expiry(service)
        return days_until_expiry <= 30
    
    @classmethod
    def get_service_status(cls, service: ClientService) -> str:
        if not service.is_active:
            return 'inactive'
        
        if cls.is_service_expired(service):
            return 'expired'
        
        days_left = cls.days_until_expiry(service)
        if days_left <= 7:
            return 'expiring_soon'
        elif days_left <= 30:
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
                'label': f'Renovar en {days_left} días',
                'class': 'badge-warning',
                'icon': 'exclamation-triangle',
                'color': 'yellow'
            },
            'expiring_soon': {
                'label': f'Vence en {days_left} días',
                'class': 'badge-danger',
                'icon': 'clock',
                'color': 'orange'
            },
            'expired': {
                'label': 'Vencido',
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
    def _get_service_active_until(cls, service: ClientService) -> date:
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
