from typing import Optional, Dict, Any
from datetime import date
from django.utils import timezone

from ..models import ClientService, ServicePayment
from .date_calculator import DateCalculator


class ServiceStateCalculator:
    
    @classmethod
    def get_service_active_until(cls, service: ClientService) -> Optional[date]:
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
    def is_service_active(cls, service: ClientService) -> bool:
        active_until = cls.get_service_active_until(service)
        if not active_until:
            return False
        return active_until >= timezone.now().date()
    
    @classmethod
    def is_service_expired(cls, service: ClientService) -> bool:
        return not cls.is_service_active(service)
    
    @classmethod
    def days_until_expiry(cls, service: ClientService) -> Optional[int]:
        active_until = cls.get_service_active_until(service)
        return DateCalculator.calculate_days_until(active_until)
    
    @classmethod
    def days_since_expiry(cls, service: ClientService) -> Optional[int]:
        if cls.is_service_active(service):
            return None
        active_until = cls.get_service_active_until(service)
        return DateCalculator.calculate_days_since(active_until)
    
    @classmethod
    def needs_renewal(cls, service: ClientService) -> bool:
        days_until = cls.days_until_expiry(service)
        if days_until is None:
            return True
        return days_until <= 7
    
    @classmethod
    def get_service_status(cls, service: ClientService) -> str:
        if cls.is_service_active(service):
            return 'ACTIVE'
        elif cls.is_service_expired(service):
            return 'EXPIRED'
        else:
            return 'INACTIVE'
    
    @classmethod
    def get_status_display_data(cls, service: ClientService) -> Dict[str, Any]:
        status = cls.get_service_status(service)
        active_until = cls.get_service_active_until(service)
        days_until = cls.days_until_expiry(service)
        days_since = cls.days_since_expiry(service)
        
        status_config = {
            'ACTIVE': {
                'label': 'Activo',
                'color': 'green',
                'icon': 'check-circle'
            },
            'EXPIRED': {
                'label': 'Vencido',
                'color': 'red',
                'icon': 'x-circle'
            },
            'INACTIVE': {
                'label': 'Inactivo',
                'color': 'gray',
                'icon': 'pause-circle'
            }
        }
        
        config = status_config.get(status, status_config['INACTIVE'])
        days_left = days_until if status == 'ACTIVE' else (days_since * -1 if days_since else None)
        
        return {
            'status': status,
            'label': config['label'],
            'color': config['color'],
            'icon': config['icon'],
            'active_until': active_until,
            'days_until_expiry': days_until,
            'days_since_expiry': days_since,
            'days_left': days_left,
            'needs_renewal': cls.needs_renewal(service),
            'is_active': status == 'ACTIVE',
            'is_expired': status == 'EXPIRED'
        }
