from typing import Optional, Tuple
from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone

from ..models import ClientService, ServicePayment


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
            payment_date = timezone.now().date()

        current_active_until = cls.get_service_active_until(client_service)
        
        if current_active_until and current_active_until >= payment_date:
            period_start = current_active_until + timedelta(days=1)
        else:
            period_start = payment_date
        
        period_end = cls._add_months_to_date(period_start, extend_months)
        
        payment = ServicePayment.objects.create(
            client_service=client_service,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            reference_number=reference_number or '',
            notes=notes or '',
            status=ServicePayment.StatusChoices.PAID,
            period_start=period_start,
            period_end=period_end
        )
        
        if not client_service.is_active:
            client_service.is_active = True
            client_service.save()
        
        if period_end > client_service.end_date:
            client_service.end_date = period_end
            client_service.status = ClientService.StatusChoices.ACTIVE
            client_service.save()

        return payment
    
    @classmethod
    def extend_service_without_payment(
        cls,
        client_service: ClientService,
        extend_months: int,
        notes: Optional[str] = None
    ) -> ClientService:
        
        current_end = client_service.end_date or timezone.now().date()
        new_end = cls._add_months_to_date(current_end, extend_months)
        
        client_service.end_date = new_end
        client_service.status = ClientService.StatusChoices.ACTIVE
        client_service.is_active = True
        
        if notes:
            existing_notes = client_service.notes or ""
            client_service.notes = f"{existing_notes}\nExtensión: {notes}".strip()
        
        client_service.save()
        return client_service
    
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
        
        return ServicePayment.objects.create(
            client_service=client_service,
            amount=amount,
            payment_date=payment_date or timezone.now().date(),
            payment_method=payment_method,
            reference_number=reference_number or '',
            notes=notes or '',
            status=ServicePayment.StatusChoices.PAID,
            period_start=coverage_start,
            period_end=coverage_end
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
    
    @classmethod
    def _add_months_to_date(cls, base_date: date, months: int) -> date:
        year = base_date.year
        month = base_date.month + months
        day = base_date.day
        
        while month > 12:
            month -= 12
            year += 1
        
        try:
            return date(year, month, day)
        except ValueError:
            return date(year, month + 1, 1) - timedelta(days=1)
