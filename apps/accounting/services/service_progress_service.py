from typing import Dict, Any
from django.utils import timezone
from ..models import ClientService


class ServiceProgressService:
    """
    Servicio para gestionar y calcular el progreso de un servicio.
    Centraliza la lógica de estado de progreso para evitar redundancia.
    """
    
    @classmethod
    def get_service_progress_data(cls, service: ClientService) -> Dict[str, Any]:
        """
        Obtiene todos los datos de progreso de un servicio de forma centralizada.
        """
        return {
            'has_payments': cls._has_payments(service),
            'is_active': cls._is_active(service),
            'needs_payment': cls._needs_payment(service),
            'next_step_message': cls._get_next_step_message(service)
        }
    
    @classmethod
    def _has_payments(cls, service: ClientService) -> bool:
        """Verifica si el servicio tiene pagos registrados."""
        return service.payments.filter(
            status__in=['PAID', 'PENDING']
        ).exists()
    
    @classmethod
    def _is_active(cls, service) -> bool:
        from .service_state_manager import ServiceStateManager
        return ServiceStateManager.is_service_active(service)
    
    @classmethod
    def _needs_payment(cls, service) -> bool:
        if not cls._has_payments(service):
            return True
        
        if not cls._is_active(service):
            return True
        
        from .service_state_manager import ServiceStateManager
        return ServiceStateManager.needs_renewal(service)
    
    @classmethod
    def _get_next_step_message(cls, service) -> str:
        if not cls._has_payments(service):
            return "Registre el primer pago para activar el servicio"
        
        if not cls._is_active(service):
            return "El servicio requiere renovación para reactivarse"
        
        from .service_state_manager import ServiceStateManager
        status = ServiceStateManager.get_service_status(service)
        days_left = ServiceStateManager.days_until_expiry(service)
        
        if status == 'expiring_soon':
            return f"El servicio vence en {days_left} días. Considere renovar pronto"
        elif status == 'renewal_due':
            return f"El servicio vence en {days_left} días"
        
        return ""
