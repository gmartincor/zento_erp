from typing import Optional
from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone

from ..models import ClientService, ServicePayment


class PaymentManager:
    
    @classmethod
    def create_payment(
        cls,
        service: ClientService,
        amount: Decimal,
        payment_method: str,
        period_start: date,
        period_end: date,
        payment_date: Optional[date] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
        status: str = ServicePayment.StatusChoices.PAID
    ) -> ServicePayment:
        if payment_date is None and status == ServicePayment.StatusChoices.PAID:
            payment_date = timezone.now().date()

        return ServicePayment.objects.create(
            client_service=service,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            reference_number=reference_number or '',
            notes=notes or '',
            status=status,
            period_start=period_start,
            period_end=period_end
        )
    
    @classmethod
    def get_service_total_paid(cls, service: ClientService) -> Decimal:
        total = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).aggregate(
            total=models.Sum('amount')
        )['total']
        return total or Decimal('0.00')
    
    @classmethod
    def get_service_payment_count(cls, service: ClientService) -> int:
        return service.payments.filter(status=ServicePayment.StatusChoices.PAID).count()
    
    @classmethod
    def get_latest_payment(cls, service: ClientService) -> Optional[ServicePayment]:
        return service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-payment_date').first()
    
    @classmethod
    def get_service_current_amount(cls, service: ClientService) -> Decimal:
        latest_payment = cls.get_latest_payment(service)
        return latest_payment.amount if latest_payment else service.price
    
    @classmethod
    def get_service_current_payment_method(cls, service: ClientService) -> Optional[str]:
        latest_payment = cls.get_latest_payment(service)
        return latest_payment.payment_method if latest_payment else None
    
    @classmethod
    def get_payment_history(cls, service: ClientService):
        return service.payments.all().order_by('-payment_date')
