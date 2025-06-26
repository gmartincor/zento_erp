from typing import Optional, Dict, Any
from datetime import date
from django.utils import timezone

from ..models import ClientService
from .date_calculator import DateCalculator


class ServiceManager:
    
    @classmethod
    def can_edit_service_dates(cls, service: ClientService) -> bool:
        return not cls._has_overlapping_payments(service)
    
    @classmethod
    def get_date_edit_restrictions(cls, service: ClientService) -> Dict[str, Any]:
        
        can_edit = cls.can_edit_service_dates(service)
        
        if not can_edit:
            return {
                'can_edit_dates': False,
                'restriction_reason': 'No se pueden modificar las fechas porque el servicio tiene pagos asociados que se superponen con el período actual.'
            }
        
        return {
            'can_edit_dates': True,
            'restriction_reason': None
        }
    
    @classmethod
    def update_service_dates(
        cls, 
        service: ClientService, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> bool:
        
        if not cls.can_edit_service_dates(service):
            return False
        
        update_fields = ['updated']
        
        if start_date and start_date != service.start_date:
            service.start_date = start_date
            update_fields.append('start_date')
        
        if end_date and end_date != service.end_date:
            service.end_date = end_date
            update_fields.append('end_date')
        
        if len(update_fields) > 1:
            service.save(update_fields=update_fields)
        
        return True
    
    @classmethod
    def extend_service_without_payment(
        cls,
        service: ClientService,
        extension_months: int,
        notes: Optional[str] = None
    ) -> ClientService:
        
        from .payment_service import PaymentService
        return PaymentService.extend_service_without_payment(
            service, extension_months, notes
        )
    
    @classmethod
    def _has_overlapping_payments(cls, service: ClientService) -> bool:
        from ..models import ServicePayment
        
        return service.payments.filter(
            status=ServicePayment.StatusChoices.PAID,
            period_start__lte=service.end_date or timezone.now().date(),
            period_end__gte=service.start_date or timezone.now().date()
        ).exists()
