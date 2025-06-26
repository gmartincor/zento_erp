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
    def _is_active(cls, service: ClientService) -> bool:
        """Verifica si el servicio está activo."""
        if not service.is_active:
            return False
        
        if service.status == ClientService.StatusChoices.ACTIVE:
            if service.end_date:
                return service.end_date >= timezone.now().date()
            return True
        
        return False
    
    @classmethod
    def _needs_payment(cls, service: ClientService) -> bool:
        """Verifica si el servicio necesita un pago para continuar."""
        # Si no hay pagos, necesita pago
        if not cls._has_payments(service):
            return True
        
        # Si está inactivo pero tiene pagos, podría necesitar renovación
        if not cls._is_active(service):
            return True
        
        # Si está próximo a vencer, necesita renovación
        if service.end_date:
            days_until_expiry = (service.end_date - timezone.now().date()).days
            return days_until_expiry <= 30
        
        return False
    
    @classmethod
    def _get_next_step_message(cls, service: ClientService) -> str:
        """Obtiene el mensaje del siguiente paso a realizar."""
        if not cls._has_payments(service):
            return "Registre el primer pago para activar el servicio"
        
        if not cls._is_active(service):
            return "El servicio requiere renovación para reactivarse"
        
        if service.end_date:
            days_until_expiry = (service.end_date - timezone.now().date()).days
            if days_until_expiry <= 7:
                return f"El servicio vence en {days_until_expiry} días. Considere renovar pronto"
            elif days_until_expiry <= 30:
                return f"El servicio vence en {days_until_expiry} días"
        
        return ""
