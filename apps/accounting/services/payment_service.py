from typing import Optional, Tuple
from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone

from ..models import ClientService, ServicePayment
from .date_calculator import DateCalculator
from .payment_components import (
    PaymentPeriodCalculator, 
    PaymentCreator, 
    ServiceExtensionManager
)


class PaymentService:
    
    @classmethod
    @transaction.atomic
    def create_payment_and_extend_service(
        cls,
        client_service: ClientService,
        amount: Decimal,
        payment_method: str,
        payment_date: Optional[date] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
        extend_months: int = 1
    ) -> ServicePayment:
        
        if payment_date is None:
            payment_date = DateCalculator.get_today()

        period_start, period_end = PaymentPeriodCalculator.calculate_payment_period(
            client_service, payment_date, extend_months
        )
        
        payment = PaymentCreator.create_payment(
            service=client_service,
            amount=amount,
            payment_method=payment_method,
            period_start=period_start,
            period_end=period_end,
            payment_date=payment_date,
            reference_number=reference_number,
            notes=notes
        )
        
        ServiceExtensionManager.extend_service_to_date(client_service, period_end)
        
        return payment
    
    @classmethod
    @transaction.atomic
    def create_payment_without_extension(
        cls,
        client_service: ClientService,
        amount: Decimal,
        payment_method: str,
        period_start: date,
        period_end: date,
        payment_date: Optional[date] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ServicePayment:
        
        return PaymentCreator.create_payment(
            service=client_service,
            amount=amount,
            payment_method=payment_method,
            period_start=period_start,
            period_end=period_end,
            payment_date=payment_date,
            reference_number=reference_number,
            notes=notes
        )
    
    @classmethod
    def extend_service_without_payment(
        cls,
        client_service: ClientService,
        extend_months: int,
        notes: Optional[str] = None
    ) -> ClientService:
        
        service = ServiceExtensionManager.extend_service_by_months(client_service, extend_months)
        
        if notes:
            existing_notes = service.notes or ""
            service.notes = f"{existing_notes}\nExtensión: {notes}".strip()
            service.save()
        
        return service
    
    @classmethod
    def create_standalone_payment(
        cls,
        client_service: ClientService,
        amount: Decimal,
        payment_method: str,
        coverage_start: date,
        coverage_end: date,
        payment_date: Optional[date] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ServicePayment:
        
        return PaymentCreator.create_payment(
            service=client_service,
            amount=amount,
            payment_method=payment_method,
            period_start=coverage_start,
            period_end=coverage_end,
            payment_date=payment_date,
            reference_number=reference_number,
            notes=notes
        )
    
    @classmethod
    def get_service_active_until(cls, service: ClientService) -> Optional[date]:
        latest_payment = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-period_end').first()
        
        service_end_date = service.end_date
        
        if latest_payment and service_end_date:
            return max(latest_payment.period_end, service_end_date)
        elif latest_payment:
            return latest_payment.period_end
        else:
            return service_end_date
    
    @classmethod
    def get_service_total_paid(cls, service: ClientService) -> Decimal:
        total = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).aggregate(total=models.Sum('amount'))['total']
        return total or Decimal('0.00')
    
    @classmethod
    def get_service_payment_count(cls, service: ClientService) -> int:
        return service.payments.filter(status=ServicePayment.StatusChoices.PAID).count()
    
    @classmethod
    def get_service_current_amount(cls, service: ClientService) -> Decimal:
        latest_payment = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-payment_date').first()
        return latest_payment.amount if latest_payment else service.price
    
    @classmethod
    def get_service_current_payment_method(cls, service: ClientService) -> Optional[str]:
        latest_payment = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-payment_date').first()
        return latest_payment.payment_method if latest_payment else None
    
    @classmethod
    def analyze_payment_timing(cls, service: ClientService) -> dict:
        payments = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('period_start')
        
        late_payments = []
        on_time_payments = []
        
        for payment in payments:
            if payment.payment_date > payment.period_end:
                late_payments.append({
                    'payment': payment,
                    'days_late': (payment.payment_date - payment.period_end).days
                })
            else:
                on_time_payments.append(payment)
        
        return {
            'total_payments': payments.count(),
            'late_payments': late_payments,
            'on_time_payments': on_time_payments,
            'has_late_payments': len(late_payments) > 0
        }
