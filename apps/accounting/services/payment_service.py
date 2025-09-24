from datetime import date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models

from ..models import ClientService, ServicePayment


class PaymentService:
    @staticmethod
    def process_payment(
        period: ServicePayment,
        amount: Decimal,
        payment_date: date,
        payment_method: str,
        reference_number: str = "",
        notes: str = "",
        remanente: Optional[Decimal] = None
    ) -> ServicePayment:
        if not period.can_be_paid:
            raise ValidationError(
                f"El período con estado '{period.get_status_display()}' no puede recibir pagos"
            )
        
        PaymentService._validate_payment_data(amount, payment_date, payment_method)
        
        period.amount = amount
        period.payment_date = payment_date
        period.payment_method = payment_method
        period.reference_number = reference_number
        period.status = ServicePayment.StatusChoices.PAID
        
        # Asignar remanente si se proporciona
        if remanente is not None:
            period.remanente = remanente
        
        if notes:
            from .notes_manager import ServiceNotesManager
            period.notes = ServiceNotesManager.add_note(
                period.notes, 
                f"Pago: {notes}"
            )
        
        period.save()
        
        return period
    
    @staticmethod
    def create_payment_with_period(
        client_service: ClientService,
        amount: Decimal,
        payment_date: date,
        payment_method: str,
        period_start: date,
        period_end: date,
        reference_number: str = "",
        notes: str = "",
        remanente: Optional[Decimal] = None
    ) -> ServicePayment:
        PaymentService._validate_payment_data(amount, payment_date, payment_method)
        
        if period_start >= period_end:
            raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin")
        
        payment_period = ServicePayment.objects.create(
            client_service=client_service,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            reference_number=reference_number,
            period_start=period_start,
            period_end=period_end,
            status=ServicePayment.StatusChoices.PAID,
            notes=notes,
            remanente=remanente
        )
        
        return payment_period
    
    @staticmethod
    def get_payment_options_for_service(client_service: ClientService) -> Dict[str, Any]:
        from .period_service import ServicePeriodManager
        
        pending_periods = ServicePeriodManager.get_pending_periods(client_service)
        
        return {
            'pending_periods': [
                {
                    'id': period.id,
                    'period_start': period.period_start,
                    'period_end': period.period_end,
                    'duration_days': period.duration_days,
                    'status': period.status,
                    'display_text': f"{period.period_start} - {period.period_end} ({period.duration_days} días)"
                }
                for period in pending_periods
            ],
            'has_pending': pending_periods.exists(),
            'total_pending': pending_periods.count()
        }
    
    @staticmethod
    def calculate_suggested_amount(period: ServicePayment, client_service: ClientService) -> Optional[Decimal]:
        last_payment = client_service.payments.filter(
            status=ServicePayment.StatusChoices.PAID,
            amount__isnull=False
        ).order_by('-payment_date').first()
        
        if not last_payment:
            return None
        
        if last_payment.duration_days > 0:
            daily_rate = last_payment.amount / last_payment.duration_days
            suggested_amount = daily_rate * period.duration_days
            return round(suggested_amount, 2)
        
        return last_payment.amount
    
    @staticmethod
    def get_payment_history(client_service: ClientService) -> List[ServicePayment]:
        return client_service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-payment_date', '-period_start')
    
    @staticmethod
    def _validate_payment_data(amount: Decimal, payment_date: date, payment_method: str) -> None:
        if amount <= 0:
            raise ValidationError("El importe debe ser mayor a cero")
        
        if payment_date > timezone.now().date():
            raise ValidationError("La fecha de pago no puede ser futura")
        
        valid_methods = [choice[0] for choice in ServicePayment.PaymentMethodChoices.choices]
        if payment_method not in valid_methods:
            raise ValidationError(f"Método de pago inválido: {payment_method}")
    
    @staticmethod
    def get_service_total_paid(client_service: ClientService) -> Decimal:
        from django.db.models import Case, When, F, Sum
        
        total = client_service.payments.filter(
            status__in=[ServicePayment.StatusChoices.PAID, ServicePayment.StatusChoices.REFUNDED],
            amount__isnull=False
        ).aggregate(
            total=Sum(F('amount') - F('refunded_amount'))
        )['total']
        return total or Decimal('0.00')
    
    @staticmethod
    def get_service_payment_count(client_service: ClientService) -> int:
        return client_service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).count()
    
    @staticmethod
    def get_current_amount(client_service: ClientService) -> Optional[Decimal]:
        latest_payment = client_service.payments.filter(
            status=ServicePayment.StatusChoices.PAID,
            amount__isnull=False
        ).order_by('-payment_date').first()
        return latest_payment.amount if latest_payment else None
    
    @staticmethod
    def analyze_payment_timing(client_service: ClientService) -> Dict[str, Any]:
        payments = client_service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('payment_date')
        
        if not payments.exists():
            return {
                'average_days_between_payments': None,
                'payment_frequency': 'No payments',
                'last_payment_days_ago': None
            }
        
        if payments.count() == 1:
            last_payment = payments.first()
            days_since_last = (timezone.now().date() - last_payment.payment_date).days
            return {
                'average_days_between_payments': None,
                'payment_frequency': 'Single payment',
                'last_payment_days_ago': days_since_last
            }
        
        payment_dates = [p.payment_date for p in payments]
        intervals = [(payment_dates[i] - payment_dates[i-1]).days 
                    for i in range(1, len(payment_dates))]
        avg_interval = sum(intervals) / len(intervals)
        
        last_payment = payments.last()
        days_since_last = (timezone.now().date() - last_payment.payment_date).days
        
        if avg_interval <= 40:
            frequency = 'Monthly'
        elif avg_interval <= 100:
            frequency = 'Quarterly'
        else:
            frequency = 'Irregular'
        
        return {
            'average_days_between_payments': round(avg_interval, 1),
            'payment_frequency': frequency,
            'last_payment_days_ago': days_since_last
        }
    
    @staticmethod
    def get_service_current_amount(client_service: ClientService) -> Optional[Decimal]:
        return PaymentService.get_current_amount(client_service)
    
    @staticmethod
    def get_service_current_payment_method(client_service: ClientService) -> Optional[str]:
        latest_payment = client_service.payments.filter(
            status=ServicePayment.StatusChoices.PAID,
            payment_method__isnull=False
        ).order_by('-payment_date').first()
        return latest_payment.payment_method if latest_payment else None
    
    @staticmethod
    def calculate_revenue_stats(payments_queryset) -> Dict[str, Any]:
        from django.db.models import Sum, Count, F, Q
        from decimal import Decimal
        
        valid_payments = payments_queryset.filter(amount__isnull=False)
        
        summary = valid_payments.aggregate(
            total_amount=Sum(F('amount') - F('refunded_amount')),
            total_payments=Count('id', filter=Q(status=ServicePayment.StatusChoices.PAID)),
        )
        
        total_amount = summary['total_amount'] or Decimal('0')
        total_payments = summary['total_payments'] or 0
        
        return {
            'total_amount': total_amount,
            'total_payments': total_payments,
            'average_amount': total_amount / total_payments if total_payments > 0 else Decimal('0'),
        }
    
    @staticmethod
    def update_payment(
        payment: ServicePayment,
        amount: Decimal,
        payment_date: date,
        payment_method: str,
        reference_number: str = "",
        notes: str = "",
        remanente: Optional[Decimal] = None
    ) -> ServicePayment:
        if payment.status != ServicePayment.StatusChoices.PAID:
            raise ValidationError("Solo se pueden editar pagos con estado PAGADO.")
        
        PaymentService._validate_payment_data(amount, payment_date, payment_method)
        
        original_amount = payment.amount
        
        payment.amount = amount
        payment.payment_date = payment_date
        payment.payment_method = payment_method
        payment.reference_number = reference_number
        payment.notes = notes
        
        if remanente is not None:
            if payment.client_service.category != ClientService.CategoryChoices.BUSINESS:
                raise ValidationError("Los remanentes solo pueden aplicarse a servicios BUSINESS.")
            payment.remanente = remanente
        
        payment.save()
        
        return payment
