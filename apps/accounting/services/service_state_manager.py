from typing import Dict, Any
from ..models import ClientService
from .service_state_calculator import ServiceStateCalculator


class ServiceStateManager:
    
    @classmethod
    def is_service_active(cls, service: ClientService) -> bool:
        return ServiceStateCalculator.is_service_active(service)
    
    @classmethod
    def is_service_expired(cls, service: ClientService) -> bool:
        return ServiceStateCalculator.is_service_expired(service)
    
    @classmethod
    def days_until_expiry(cls, service: ClientService) -> int:
        return ServiceStateCalculator.days_until_expiry(service)
    
    @classmethod
    def needs_renewal(cls, service: ClientService) -> bool:
        return ServiceStateCalculator.needs_renewal(service)
    
    @classmethod
    def get_service_status(cls, service: ClientService) -> str:
        return ServiceStateCalculator.get_service_status(service)
    
    @classmethod
    def get_status_display_data(cls, service: ClientService) -> Dict[str, Any]:
        return ServiceStateCalculator.get_status_display_data(service)
    
    @classmethod
    def get_status_priority(cls, status: str) -> int:
        priorities = {
            'EXPIRED': 1,
            'INACTIVE': 2,
            'ACTIVE': 3,
        }
        return priorities.get(status, 0)
