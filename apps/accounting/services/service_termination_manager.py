from typing import Optional
from datetime import date
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..models import ClientService


class ServiceTerminationManager:
    
    @staticmethod
    @transaction.atomic
    def terminate_service(service: ClientService, termination_date: Optional[date] = None, 
                         reason: Optional[str] = None) -> ClientService:
        if not service.is_active:
            raise ValidationError("El servicio ya está inactivo")
        
        termination_date = termination_date or timezone.now().date()
        today = timezone.now().date()
        
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
