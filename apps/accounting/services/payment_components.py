from typing import Optional, Tuple, Dict, Any
from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from ..models import ClientService, ServicePayment
from .date_calculator import DateCalculator


class PaymentPeriodCalculator:
    
    @staticmethod
    def calculate_payment_period(
        service: ClientService,
        payment_date: date,
        months: int = 1,
        start_from_service_end: bool = True
    ) -> Tuple[date, date]:
        
        if start_from_service_end and service.end_date:
            current_end = service.end_date
            if current_end >= payment_date:
                period_start = current_end + timedelta(days=1)
            else:
                period_start = payment_date
        else:
            period_start = payment_date
        
        period_end = DateCalculator.add_months_to_date(period_start, months)
        return period_start, period_end
    
    @staticmethod
    def calculate_custom_period(
        start_date: date,
        end_date: date
    ) -> Tuple[date, date]:
        return start_date, end_date
    
    @staticmethod
    def get_next_available_period_start(service: ClientService) -> date:
        latest_payment = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-period_end').first()
        
        if latest_payment:
            return latest_payment.period_end + timedelta(days=1)
        
        return service.start_date or DateCalculator.get_today()


class PaymentValidator:
    
    @staticmethod
    def validate_payment_data(
        service: ClientService,
        amount: Decimal,
        period_start: date,
        period_end: date,
        payment_date: date
    ) -> Dict[str, Any]:
        errors = []
        
        if amount <= 0:
            errors.append("El monto debe ser mayor a cero")
        
        if period_start >= period_end:
            errors.append("La fecha de fin debe ser posterior a la fecha de inicio")
        
        if payment_date > period_end:
            errors.append("La fecha de pago no puede ser posterior al fin del período")
        
        overlapping = PaymentValidator._check_period_overlap(service, period_start, period_end)
        if overlapping:
            errors.append("El período se superpone con un pago existente")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def _check_period_overlap(
        service: ClientService,
        period_start: date,
        period_end: date
    ) -> bool:
        return service.payments.filter(
            status=ServicePayment.StatusChoices.PAID,
            period_start__lt=period_end,
            period_end__gt=period_start
        ).exists()


class ServiceExtensionManager:
    
    @staticmethod
    @transaction.atomic
    def extend_service_to_date(service: ClientService, new_end_date: date) -> ClientService:
        if not service.end_date or new_end_date > service.end_date:
            service.end_date = new_end_date
            service.status = ClientService.StatusChoices.ACTIVE
            service.is_active = True
            service.save()
        
        return service
    
    @staticmethod
    @transaction.atomic
    def extend_service_by_months(service: ClientService, months: int) -> ClientService:
        current_end = service.end_date or DateCalculator.get_today()
        new_end = DateCalculator.add_months_to_date(current_end, months)
        return ServiceExtensionManager.extend_service_to_date(service, new_end)


class PaymentCreator:
    
    @staticmethod
    @transaction.atomic
    def create_payment(
        service: ClientService,
        amount: Decimal,
        payment_method: str,
        period_start: date,
        period_end: date,
        payment_date: Optional[date] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ServicePayment:
        
        if payment_date is None:
            payment_date = DateCalculator.get_today()
        
        validation = PaymentValidator.validate_payment_data(
            service, amount, period_start, period_end, payment_date
        )
        
        if not validation['is_valid']:
            raise ValueError(f"Datos de pago inválidos: {', '.join(validation['errors'])}")
        
        payment = ServicePayment.objects.create(
            client_service=service,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            reference_number=reference_number or '',
            notes=notes or '',
            status=ServicePayment.StatusChoices.PAID,
            period_start=period_start,
            period_end=period_end
        )
        
        if not service.is_active:
            service.is_active = True
            service.save()
        
        return payment
