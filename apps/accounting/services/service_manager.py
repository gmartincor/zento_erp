from typing import NamedTuple
from ..models import ClientService, ServicePayment
from .service_state_manager import ServiceStateManager


class DateEditRestrictions(NamedTuple):
    can_edit_dates: bool
    restriction_reason: str = ""
    has_payments: bool = False


class ServiceManager:
    
    @classmethod
    def can_edit_service_dates(cls, service: ClientService) -> bool:
        return cls.get_date_edit_restrictions(service).can_edit_dates
    
    @classmethod 
    def get_date_edit_restrictions(cls, service: ClientService) -> DateEditRestrictions:
        if not ServiceStateManager.is_service_active(service):
            return DateEditRestrictions(
                can_edit_dates=False,
                restriction_reason="No se pueden editar fechas de servicios inactivos o deshabilitados",
                has_payments=cls._has_payments(service)
            )
        payment_info = cls._get_payment_status(service)
        
        if payment_info['has_paid']:
            return DateEditRestrictions(
                can_edit_dates=False,
                restriction_reason="Las fechas del servicio no se pueden editar ya que el servicio tiene pagos registrados",
                has_payments=True
            )
        
        if payment_info['has_any']:
            return DateEditRestrictions(
                can_edit_dates=True,
                restriction_reason="El servicio tiene períodos de pago registrados",
                has_payments=True
            )
        
        return DateEditRestrictions(
            can_edit_dates=True,
            restriction_reason="",
            has_payments=False
        )
    
    @classmethod
    def _has_payments(cls, service: ClientService) -> bool:
        return service.payments.exists()
    
    @classmethod 
    def _get_payment_status(cls, service: ClientService) -> dict:
        payments = service.payments.values_list('status', flat=True)
        
        if not payments:
            return {'has_any': False, 'has_paid': False}
        
        payment_statuses = set(payments)
        return {
            'has_any': True,
            'has_paid': ServicePayment.StatusChoices.PAID in payment_statuses
        }
