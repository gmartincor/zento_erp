from typing import Optional, Dict, Any
from datetime import date
from django.utils import timezone

from ..models import ClientService, ServicePayment
from .date_calculator import DateCalculator


class ServiceStateCalculator:
    
    @classmethod
    def get_service_active_until(cls, service: ClientService) -> Optional[date]:
        if hasattr(service, '_active_until_cache'):
            return service._active_until_cache
        
        latest_payment = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-period_end').first()
        
        active_until = latest_payment.period_end if latest_payment else service.end_date
        service._active_until_cache = active_until
        return active_until
    
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
        
        return {
            'status': status,
            'active_until': active_until,
            'days_until_expiry': days_until,
            'days_since_expiry': days_since,
            'needs_renewal': cls.needs_renewal(service),
            'is_active': status == 'ACTIVE',
            'is_expired': status == 'EXPIRED'
        }
