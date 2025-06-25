from typing import Optional, List, Tuple, Dict, Any
from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError

from ..models import ClientService, ServicePayment


class PaymentService:
    
    @classmethod
    def create_payment(
        cls,
        client_service: ClientService,
        amount: Decimal,
        period_start: date,
        period_end: date,
        payment_method: str,
        payment_date: Optional[date] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
        mark_as_paid: bool = False
    ) -> ServicePayment:
        if payment_date is None:
            payment_date = timezone.now().date()

        payment = ServicePayment(
            client_service=client_service,
            amount=amount,
            payment_date=payment_date,
            period_start=period_start,
            period_end=period_end,
            payment_method=payment_method,
            reference_number=reference_number or '',
            notes=notes or ''
        )
        
        if mark_as_paid:
            payment.status = ServicePayment.StatusChoices.PAID
        
        payment.save()
        return payment

    @classmethod
    def process_renewal(
        cls,
        client_service: ClientService,
        amount: Decimal,
        duration_months: int,
        payment_method: str,
        payment_date: Optional[date] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ServicePayment:
        if payment_date is None:
            payment_date = timezone.now().date()

        latest_payment = client_service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-period_end').first()

        if latest_payment and latest_payment.period_end >= payment_date:
            period_start = latest_payment.period_end + timedelta(days=1)
        else:
            period_start = payment_date

        period_end = cls._calculate_period_end(period_start, duration_months)

        with transaction.atomic():
            payment = cls.create_payment(
                client_service=client_service,
                amount=amount,
                period_start=period_start,
                period_end=period_end,
                payment_method=payment_method,
                payment_date=payment_date,
                reference_number=reference_number,
                notes=notes,
                mark_as_paid=True
            )

            if not client_service.is_active:
                client_service.is_active = True
                client_service.save()

        return payment
    
    @classmethod
    def validate_payment_consistency_after_service_update(cls, service: ClientService) -> Dict[str, Any]:
        validation_results = {
            'is_valid': True,
            'warnings': [],
            'recommendations': []
        }
        
        if not service.client.is_active:
            validation_results['warnings'].append(
                'El cliente asociado está inactivo. Los pagos existentes no se ven afectados.'
            )
        
        if not service.is_active:
            validation_results['warnings'].append(
                'El servicio está inactivo. Considera revisar los pagos pendientes.'
            )
        
        active_payments = service.payments.filter(status=ServicePayment.StatusChoices.PAID).count()
        if active_payments > 0:
            validation_results['recommendations'].append(
                f'Este servicio tiene {active_payments} pagos registrados. '
                'Cualquier cambio significativo puede requerir ajustes en los pagos futuros.'
            )
        
        return validation_results
    
    @classmethod
    def get_service_payment_status(cls, service: ClientService) -> str:
        latest_payment = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-period_end').first()
        
        if not latest_payment:
            return service.status
        
        today = timezone.now().date()
        if latest_payment.period_end >= today:
            return 'ACTIVE'
        else:
            return 'EXPIRED'
    
    @classmethod
    def get_service_active_until(cls, service: ClientService) -> Optional[date]:
        latest_payment = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-period_end').first()
        return latest_payment.period_end if latest_payment else service.end_date
    
    @classmethod
    def get_service_total_paid(cls, service: ClientService) -> Decimal:
        from django.db import models
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
    def get_service_current_amount(cls, service: ClientService) -> Decimal:
        latest_payment = service.payments.order_by('-created').first()
        return latest_payment.amount if latest_payment else service.price
    
    @classmethod
    def get_service_current_payment_method(cls, service: ClientService) -> Optional[str]:
        latest_payment = service.payments.order_by('-created').first()
        return latest_payment.payment_method if latest_payment else None
    
    @classmethod
    def get_service_current_dates(cls, service: ClientService) -> Dict[str, Any]:
        latest_payment = service.payments.order_by('-created').first()
        if not latest_payment:
            return {
                'start_date': service.start_date,
                'end_date': service.end_date
            }
        
        return {
            'start_date': latest_payment.period_start,
            'end_date': latest_payment.period_end
        }

    @classmethod
    def _calculate_period_end(cls, start_date: date, duration_months: int) -> date:
        year = start_date.year
        month = start_date.month + duration_months
        
        while month > 12:
            month -= 12
            year += 1
        
        try:
            period_end = date(year, month, start_date.day) - timedelta(days=1)
        except ValueError:
            period_end = date(year, month, 1) - timedelta(days=1)
        
        return period_end

    @classmethod
    def get_next_renewal_date(cls, client_service: ClientService) -> Optional[date]:
        latest_payment = client_service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-period_end').first()
        
        if latest_payment:
            return latest_payment.period_end + timedelta(days=1)
        return None

    @classmethod
    def get_overdue_payments(cls, days_overdue: int = 0) -> List[ServicePayment]:
        cutoff_date = timezone.now().date() - timedelta(days=days_overdue)
        return ServicePayment.objects.filter(
            status=ServicePayment.StatusChoices.PENDING,
            period_end__lt=cutoff_date
        ).select_related('client_service__client', 'client_service__business_line')

    @classmethod
    def mark_overdue_payments(cls, days_overdue: int = 0) -> int:
        overdue_payments = cls.get_overdue_payments(days_overdue)
        count = 0
        
        for payment in overdue_payments:
            payment.mark_as_overdue()
            count += 1
        
        return count

    @classmethod
    @classmethod
    def get_payment_history(
        cls, 
        client_service: ClientService,
        status_filter: Optional[str] = None
    ) -> List[ServicePayment]:
        queryset = client_service.payments.filter(status=ServicePayment.StatusChoices.PAID)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-payment_date')

    @classmethod
    def calculate_service_revenue(
        cls,
        client_service: ClientService,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Decimal:
        queryset = client_service.payments.filter(status=ServicePayment.StatusChoices.PAID)
        
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)
        
        total = queryset.aggregate(total=models.Sum('amount'))['total']
        return total or Decimal('0')

    @classmethod
    def get_expiring_services(cls, days_ahead: int = 30) -> List[Tuple[ClientService, ServicePayment]]:
        expiry_date = timezone.now().date() + timedelta(days=days_ahead)
        
        active_payments = ServicePayment.objects.filter(
            status=ServicePayment.StatusChoices.PAID,
            period_end__lte=expiry_date,
            period_end__gte=timezone.now().date()
        ).select_related('client_service__client', 'client_service__business_line')
        
        result = []
        processed_services = set()
        
        for payment in active_payments:
            if payment.client_service.id not in processed_services:
                latest_payment = payment.client_service.payments.filter(
                    status=ServicePayment.StatusChoices.PAID
                ).order_by('-period_end').first()
                
                if latest_payment and latest_payment.id == payment.id:
                    result.append((payment.client_service, payment))
                    processed_services.add(payment.client_service.id)
        
        return result

    @classmethod
    def validate_payment_period(
        cls,
        client_service: ClientService,
        period_start: date,
        period_end: date
    ) -> bool:
        overlapping_payments = client_service.payments.filter(
            status__in=[ServicePayment.StatusChoices.PAID, ServicePayment.StatusChoices.PENDING],
            period_start__lt=period_end,
            period_end__gt=period_start
        )
        
        return not overlapping_payments.exists()
