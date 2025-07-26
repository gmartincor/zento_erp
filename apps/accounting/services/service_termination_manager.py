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
            
        today = timezone.now().date()
        if service.end_date and service.end_date < today:
            raise ValidationError("El servicio ya ha sido finalizado anteriormente")
        
        termination_date = termination_date or today
        
        ServiceTerminationManager.validate_termination_date(service, termination_date)
        ServiceTerminationManager._delete_affected_periods(service, termination_date)
        ServiceTerminationManager._adjust_active_period(service, termination_date)
        ServiceTerminationManager._final_cleanup(service, termination_date)
        
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
    def _adjust_active_period(service: ClientService, termination_date: date) -> None:
        adjustable_periods = ServiceTerminationManager._get_adjustable_periods(service, termination_date)
        
        for period in adjustable_periods:
            period.period_end = termination_date
            period.save(update_fields=['period_end', 'modified'])

    @staticmethod
    def can_terminate_service(service: ClientService) -> bool:
        if not service.is_active:
            return False
            
        today = timezone.now().date()
        if service.end_date and service.end_date < today:
            return False
            
        return True
    
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
    def _get_deletable_periods(service: ClientService, termination_date: date):
        return service.payments.filter(period_start__gt=termination_date)
    
    @staticmethod
    def _get_adjustable_periods(service: ClientService, termination_date: date):
        return service.payments.filter(
            period_start__lte=termination_date,
            period_end__gt=termination_date
        )
    
    @staticmethod
    def _delete_affected_periods(service: ClientService, termination_date: date) -> None:
        future_periods = ServiceTerminationManager._get_deletable_periods(service, termination_date)
        future_periods.delete()
    
    @staticmethod
    def _final_cleanup(service: ClientService, termination_date: date) -> None:
        remaining_future_periods = service.payments.filter(period_end__gt=termination_date)
        if remaining_future_periods.exists():
            for period in remaining_future_periods:
                if period.period_start > termination_date:
                    period.delete()
                else:
                    period.period_end = termination_date
                    period.save(update_fields=['period_end', 'modified'])
    
    @staticmethod
    def get_affected_payments_info(service: ClientService, termination_date: date) -> dict:
        future_periods = ServiceTerminationManager._get_deletable_periods(service, termination_date)
        adjustable_periods = ServiceTerminationManager._get_adjustable_periods(service, termination_date)
        
        return {
            'future_periods': future_periods,
            'adjustable_periods': adjustable_periods,
            'future_count': future_periods.count(),
            'adjustable_count': adjustable_periods.count(),
            'total_affected': future_periods.count() + adjustable_periods.count()
        }
