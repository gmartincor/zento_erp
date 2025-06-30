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
        
        # Validar la fecha de finalización
        ServiceTerminationManager.validate_termination_date(service, termination_date)
        
        # La fecha de finalización es el último día que el servicio está activo
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
    @transaction.atomic
    def reactivate_service(service: ClientService) -> ClientService:
        if service.is_active:
            raise ValidationError("El servicio ya está activo")
        
        service.is_active = True
        service.end_date = None
        service.save()
        return service
    
    @staticmethod
    def can_terminate_service(service: ClientService) -> bool:
        return service.is_active
    
    @staticmethod
    def can_reactivate_service(service: ClientService) -> bool:
        return not service.is_active and service.end_date is not None
    
    @staticmethod
    def get_termination_date_limits(service: ClientService) -> dict:
        """
        Obtiene los límites de fecha para la finalización de un servicio.
        
        Returns:
            dict: {
                'min_date': fecha mínima permitida (día después del inicio),
                'max_date': fecha máxima permitida (último período pagado),
                'has_paid_periods': si tiene períodos pagados,
                'last_paid_date': fecha del último período pagado
            }
        """
        limits = {
            'min_date': None,
            'max_date': None,
            'has_paid_periods': False,
            'last_paid_date': None
        }
        
        # Fecha mínima: día después del inicio del servicio
        if service.start_date:
            limits['min_date'] = service.start_date + timedelta(days=1)
        
        # Fecha máxima: último período creado (incluye creados, pendientes y pagados)
        last_created_payment = service.payments.filter(
            status__in=[
                ServicePayment.StatusChoices.PERIOD_CREATED,
                ServicePayment.StatusChoices.PENDING,
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
        limits = ServiceTerminationManager.get_termination_date_limits(service)
        
        if limits['has_paid_periods']:
            return limits['last_paid_date']
        
        return service.end_date
    
    @staticmethod
    def validate_termination_date(service: ClientService, termination_date: date) -> None:
  
        limits = ServiceTerminationManager.get_termination_date_limits(service)
        
        # Validar fecha mínima
        if limits['min_date'] and termination_date <= service.start_date:
            raise ValidationError(
                f"La fecha de finalización debe ser posterior al {service.start_date.strftime('%d/%m/%Y')}"
            )
        
        # Validar fecha máxima (solo si hay períodos creados)
        if limits['max_date'] and termination_date > limits['max_date']:
            raise ValidationError(
                f"No puedes finalizar el servicio más allá del último período creado "
                f"({limits['max_date'].strftime('%d/%m/%Y')}). "
                f"Si necesitas extender el servicio, primero crea un nuevo período."
            )
