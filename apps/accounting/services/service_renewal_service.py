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
        from .service_state_calculator import ServiceStateCalculator
        from .date_calculator import DateCalculator
        from .payment_manager import PaymentManager
        
        if payment_date is None:
            payment_date = timezone.now().date()
        
        with transaction.atomic():
            current_active_until = ServiceStateCalculator.get_service_active_until(service)
            
            if current_active_until:
                period_start = current_active_until + timedelta(days=1)
                period_end = DateCalculator.add_months_to_date(current_active_until, duration_months)
            else:
                period_start = payment_date
                period_end = DateCalculator.add_months_to_date(payment_date, duration_months)
            
            payment = PaymentManager.create_payment(
                service=service,
                amount=amount,
                payment_method=payment_method,
                period_start=period_start,
                period_end=period_end,
                payment_date=payment_date,
                reference_number=reference_number,
                notes=notes
            )
            
            if not service.is_active:
                service.is_active = True
                service.save()
            
            service.get_fresh_service_data()
        
        return payment

    @classmethod
    def extend_service_without_payment(
        cls,
        service: ClientService,
        duration_months: int = 1,
        notes: Optional[str] = None
    ) -> date:
        from .service_state_calculator import ServiceStateCalculator
        from .date_calculator import DateCalculator
        
        with transaction.atomic():
            current_active_until = ServiceStateCalculator.get_service_active_until(service)
            
            if current_active_until:
                new_end_date = DateCalculator.add_months_to_date(current_active_until, duration_months)
            else:
                new_end_date = DateCalculator.add_months_to_date(service.end_date or timezone.now().date(), duration_months)
            
            service.end_date = new_end_date
            service.status = ClientService.StatusChoices.ACTIVE
            service.is_active = True
            
            if notes:
                existing_notes = service.notes or ""
                service.notes = f"{existing_notes}\nExtensión sin pago: {notes}".strip()
            service.save()
            
            service.get_fresh_service_data()
        
        return new_end_date

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
                from .payment_manager import PaymentManager
                payment = PaymentManager.create_payment(
                    service=new_service,
                    amount=amount,
                    payment_method=payment_method,
                    period_start=start_date,
                    period_end=end_date,
                    payment_date=payment_date,
                    reference_number=reference_number,
                    notes=notes
                )

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
    def extend_service_flexible(
        cls,
        service: ClientService,
        amount: Decimal,
        duration_months: int = 1,
        payment_date: Optional[date] = None,
        payment_method: Optional[str] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[Optional[ServicePayment], date]:
        if payment_method and payment_date:
            payment = cls.extend_current_service(
                service=service,
                amount=amount,
                payment_method=payment_method,
                duration_months=duration_months,
                payment_date=payment_date,
                reference_number=reference_number,
                notes=notes
            )
            return payment, payment.period_end
        else:
            new_end_date = cls.extend_service_without_payment(
                service=service,
                duration_months=duration_months,
                notes=notes
            )
            return None, new_end_date

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
