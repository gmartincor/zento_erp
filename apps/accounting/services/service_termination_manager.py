from typing import Optional
from datetime import date, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..models import ClientService, ServicePayment


class ServiceTerminationManager:
    
    @staticmethod
    @transaction.atomic
    def terminate_service(service: ClientService, termination_date: Optional[date] = None, 
                         reason: Optional[str] = None) -> ClientService:
        if not service.is_active:
            raise ValidationError("El servicio ya está inactivo")
        
        termination_date = termination_date or timezone.now().date()
        today = timezone.now().date()
        
        ServiceTerminationManager.validate_termination_date(service, termination_date)
        ServiceTerminationManager._cancel_affected_periods(service, termination_date)
        
        service.end_date = termination_date
        
        if termination_date <= today:
            service.is_active = False
        
        if reason:
            current_notes = service.notes or ""
            termination_note = f"Servicio finalizado el {termination_date.strftime('%d/%m/%Y')}"
            if reason:
                termination_note += f" - Motivo: {reason}"
            
            service.notes = f"{current_notes}\n{termination_note}".strip()
        
        service.save()
        return service
    
    @staticmethod
    def can_terminate_service(service: ClientService) -> bool:
        return service.is_active
    
    @staticmethod
    def get_termination_date_limits(service: ClientService) -> dict:
        limits = {
            'min_date': service.start_date + timedelta(days=1) if service.start_date else None,
            'max_date': None,
            'has_paid_periods': False,
            'last_paid_date': None
        }
        
        last_created_payment = service.payments.filter(
            status__in=[
                ServicePayment.StatusChoices.AWAITING_START,
                ServicePayment.StatusChoices.UNPAID_ACTIVE,
                ServicePayment.StatusChoices.PAID
            ]
        ).order_by('-period_end').first()
        
        last_paid_payment = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-period_end').first()
        
        if last_created_payment:
            limits['max_date'] = last_created_payment.period_end
        
        if last_paid_payment:
            limits['has_paid_periods'] = True
            limits['last_paid_date'] = last_paid_payment.period_end
        
        return limits
    
    @staticmethod
    def get_actual_end_date(service: ClientService) -> date:
        return service.end_date
    
    @staticmethod
    def validate_termination_date(service: ClientService, termination_date: date) -> None:
        limits = ServiceTerminationManager.get_termination_date_limits(service)
        
        if limits['min_date'] and termination_date <= service.start_date:
            raise ValidationError(
                f"La fecha de finalización debe ser posterior al {service.start_date.strftime('%d/%m/%Y')}"
            )
        
        if limits['max_date'] and termination_date > limits['max_date']:
            raise ValidationError(
                f"No puedes finalizar el servicio más allá del último período creado "
                f"({limits['max_date'].strftime('%d/%m/%Y')}). "
                f"Si necesitas extender el servicio, primero crea un nuevo período."
            )
    
    @staticmethod
    def _get_cancellable_periods(service: ClientService, termination_date: date):
        return service.payments.filter(
            period_start__gt=termination_date,
            status__in=[
                ServicePayment.StatusChoices.AWAITING_START,
                ServicePayment.StatusChoices.UNPAID_ACTIVE,
                ServicePayment.StatusChoices.OVERDUE
            ]
        )
    
    @staticmethod
    def _cancel_affected_periods(service: ClientService, termination_date: date) -> None:
        future_periods = ServiceTerminationManager._get_cancellable_periods(service, termination_date)
        
        for period in future_periods:
            period.cancel(f"Servicio finalizado el {termination_date.strftime('%d/%m/%Y')}")

    @staticmethod
    def get_affected_payments_info(service: ClientService, termination_date: date) -> dict:
        future_periods = ServiceTerminationManager._get_cancellable_periods(service, termination_date)
        
        partial_periods = service.payments.filter(
            period_start__lte=termination_date,
            period_end__gt=termination_date,
            status=ServicePayment.StatusChoices.PAID
        )
        
        return {
            'future_periods': future_periods,
            'partial_periods': partial_periods,
            'future_count': future_periods.count(),
            'partial_count': partial_periods.count()
        }
