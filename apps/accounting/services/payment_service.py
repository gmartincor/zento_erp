from typing import Optional
from datetime import date
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from ..models import ClientService, ServicePayment
from .payment_manager import PaymentManager
from .date_calculator import DateCalculator
from .service_state_calculator import ServiceStateCalculator


class PaymentService:
    
    @classmethod
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

        with transaction.atomic():
            current_active_until = ServiceStateCalculator.get_service_active_until(client_service)
            
            if current_active_until and current_active_until >= payment_date:
                new_active_until = DateCalculator.add_months_to_date(current_active_until, extend_months)
            else:
                new_active_until = DateCalculator.add_months_to_date(payment_date, extend_months)
            
            payment = PaymentManager.create_payment(
                service=client_service,
                amount=amount,
                payment_method=payment_method,
                period_start=payment_date,
                period_end=new_active_until,
                payment_date=payment_date,
                reference_number=reference_number,
                notes=notes
            )
            
            if not client_service.is_active:
                client_service.is_active = True
                client_service.save()

        return payment
    
    @classmethod
    def get_service_active_until(cls, service: ClientService) -> Optional[date]:
        return ServiceStateCalculator.get_service_active_until(service)
    
    @classmethod
    def get_service_total_paid(cls, service: ClientService) -> Decimal:
        return PaymentManager.get_service_total_paid(service)
    
    @classmethod
    def get_service_payment_count(cls, service: ClientService) -> int:
        return PaymentManager.get_service_payment_count(service)
    
    @classmethod
    def get_service_current_amount(cls, service: ClientService) -> Decimal:
        return PaymentManager.get_service_current_amount(service)
    
    @classmethod
    def get_service_current_payment_method(cls, service: ClientService) -> Optional[str]:
        return PaymentManager.get_service_current_payment_method(service)
    
    @classmethod
    def get_payment_history(cls, service: ClientService):
        return PaymentManager.get_payment_history(service)
