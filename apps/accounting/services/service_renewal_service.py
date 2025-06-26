from typing import Tuple, Optional
from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from ..models import ClientService, ServicePayment
from .payment_service import PaymentService


class ServiceRenewalService:
    
    @classmethod
    def extend_current_service(
        cls,
        service: ClientService,
        amount: Decimal,
        payment_method: str,
        duration_months: int = 1,
        payment_date: Optional[date] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ServicePayment:
        if payment_date is None:
            payment_date = timezone.now().date()
        
        return PaymentService.create_payment_and_extend_service(
            client_service=service,
            amount=amount,
            payment_method=payment_method,
            payment_date=payment_date,
            reference_number=reference_number,
            notes=notes,
            extend_months=duration_months
        )

    @classmethod
    def create_manual_renewal(
        cls,
        original_service: ClientService,
        start_date: date,
        duration_months: int = 1,
        amount: Optional[Decimal] = None,
        payment_date: Optional[date] = None,
        payment_method: Optional[str] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[ClientService, Optional[ServicePayment]]:
        
        if amount is None:
            amount = original_service.price
        
        end_date = cls._calculate_end_date(start_date, duration_months)
        
        with transaction.atomic():
            new_service = ClientService.objects.create(
                client=original_service.client,
                business_line=original_service.business_line,
                category=original_service.category,
                price=amount,
                start_date=start_date,
                end_date=end_date,
                status=ClientService.StatusChoices.ACTIVE,
                notes=f"Renovación de servicio anterior. {notes or ''}".strip(),
                remanentes=original_service.remanentes,
                is_active=True
            )
            
            payment = None
            if payment_date and payment_method:
                payment = PaymentService.create_payment_and_extend_service(
                    client_service=new_service,
                    amount=amount,
                    payment_method=payment_method,
                    payment_date=payment_date,
                    reference_number=reference_number,
                    notes=notes,
                    extend_months=duration_months
                )
            else:
                PaymentService._update_service_active_until(new_service, start_date - timedelta(days=1))

        return new_service, payment

    @classmethod
    def mark_service_as_not_renewed(
        cls,
        service: ClientService,
        reason: Optional[str] = None
    ) -> bool:
        notes = f"Cliente decidió no renovar. {reason or ''}".strip()
        
        if service.notes:
            service.notes = f"{service.notes}\n{notes}"
        else:
            service.notes = notes
        
        service.status = ClientService.StatusChoices.INACTIVE
        service.save()
        
        return True

    @classmethod
    def _calculate_end_date(cls, start_date: date, months: int) -> date:
        year = start_date.year
        month = start_date.month + months
        day = start_date.day
        
        while month > 12:
            month -= 12
            year += 1
        
        try:
            return date(year, month, day) - timedelta(days=1)
        except ValueError:
            return date(year, month + 1, 1) - timedelta(days=1)
