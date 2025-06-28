from datetime import date
from decimal import Decimal
from typing import Optional
from django.db import transaction
from django.core.exceptions import ValidationError

from ..models import ServicePayment
from .payment_service import PaymentService


class DeferredPaymentService:
    
    @classmethod
    @transaction.atomic
    def process_deferred_payment(
        cls,
        period: ServicePayment,
        amount: Decimal,
        payment_date: date,
        payment_method: str,
        reference_number: str = "",
        notes: str = ""
    ) -> ServicePayment:
        
        if not period.can_be_paid:
            raise ValidationError(
                f"El período no puede recibir pagos (estado: {period.get_status_display()})"
            )
        
        if payment_date < period.period_start:
            raise ValidationError(
                "La fecha de pago no puede ser anterior al inicio del período"
            )
        
        return PaymentService.process_payment(
            period=period,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes or "Pago diferido"
        )
    
    @classmethod
    def get_pending_periods_for_payment(cls, client_service):
        return client_service.payments.filter(
            status__in=[
                ServicePayment.StatusChoices.PERIOD_CREATED,
                ServicePayment.StatusChoices.PENDING
            ]
        ).order_by('period_start')
    
    @classmethod
    def can_pay_period(cls, period: ServicePayment, payment_date: date) -> tuple[bool, str]:
        if not period.can_be_paid:
            return False, f"Estado del período no permite pagos: {period.get_status_display()}"
        
        if payment_date < period.period_start:
            return False, "La fecha de pago no puede ser anterior al inicio del período"
        
        return True, "Pago permitido"
