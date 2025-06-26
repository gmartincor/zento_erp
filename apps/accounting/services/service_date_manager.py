from typing import Dict, Any, Optional
from datetime import date, timedelta
from django.utils import timezone
from ..models import ClientService, ServicePayment


class ServiceDateManager:
    
    @classmethod
    def get_date_edit_restrictions(cls, service: ClientService) -> Dict[str, Any]:
        has_payments = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).exists()
        
        return {
            'can_edit_dates': not has_payments,
            'can_edit_start_date': not has_payments,
            'can_edit_end_date': True,
            'min_start_date': None,
            'max_start_date': timezone.now().date() if not service.pk else None,
            'min_end_date': service.start_date if service.start_date else timezone.now().date(),
            'max_end_date': None,
            'restriction_reason': 'No se pueden modificar las fechas de servicios con pagos registrados' if has_payments else None,
            'restrictions': {
                'has_payments': has_payments,
                'message': 'No se pueden modificar las fechas de servicios con pagos registrados' if has_payments else None
            }
        }
    
    @classmethod
    def validate_date_range(cls, start_date: date, end_date: Optional[date] = None) -> Dict[str, Any]:
        today = timezone.now().date()
        errors = []
        
        if start_date > today:
            errors.append('La fecha de inicio no puede ser futura')
        
        if end_date and end_date < start_date:
            errors.append('La fecha de fin debe ser posterior a la fecha de inicio')
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    @classmethod
    def calculate_service_duration(cls, start_date: date, end_date: Optional[date] = None) -> Dict[str, Any]:
        if not end_date:
            end_date = timezone.now().date()
        
        duration = (end_date - start_date).days
        months = duration // 30
        
        return {
            'days': duration,
            'months': months,
            'years': duration // 365
        }
    
    @classmethod
    def get_suggested_end_date(cls, start_date: date, duration_months: int = 12) -> date:
        year = start_date.year
        month = start_date.month + duration_months
        day = start_date.day
        
        while month > 12:
            month -= 12
            year += 1
        
        try:
            return date(year, month, day)
        except ValueError:
            return date(year, month + 1, 1) - timedelta(days=1)
