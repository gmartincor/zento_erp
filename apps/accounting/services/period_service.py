from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List
from django.utils import timezone
from django.core.exceptions import ValidationError

from ..models import ClientService, ServicePayment


class ServicePeriodManager:
    
    @staticmethod
    def create_period(
        client_service: ClientService,
        period_start: date,
        period_end: date,
        notes: str = ""
    ) -> ServicePayment:
        if period_start >= period_end:
            raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin")
        
        if ServicePeriodManager._has_overlapping_periods(client_service, period_start, period_end):
            raise ValidationError("El período se solapa con un período existente")
        
        period = ServicePayment.objects.create(
            client_service=client_service,
            period_start=period_start,
            period_end=period_end,
            status=ServicePayment.StatusChoices.PERIOD_CREATED,
            notes=notes,
            amount=None,
            payment_date=None,
            payment_method=None
        )
        
        return period
    
    @staticmethod
    def extend_service_to_date(
        client_service: ClientService,
        new_end_date: date,
        notes: str = ""
    ) -> ServicePayment:
        current_end = client_service.end_date
        
        if current_end is None:
            period_start = client_service.start_date or new_end_date
            if client_service.start_date is None:
                client_service.start_date = new_end_date
        else:
            if new_end_date <= current_end:
                raise ValidationError("La nueva fecha de fin debe ser posterior a la fecha actual")
            period_start = current_end + timedelta(days=1)
        
        period = ServicePeriodManager.create_period(
            client_service=client_service,
            period_start=period_start,
            period_end=new_end_date,
            notes=notes
        )
        
        client_service.end_date = new_end_date
        client_service.save(update_fields=['start_date', 'end_date', 'modified'])
        
        return period
    
    @staticmethod
    def extend_service(
        client_service: ClientService,
        extension_months: int,
        notes: str = ""
    ) -> ServicePayment:
        current_end = client_service.end_date
        if current_end is None:
            from datetime import date
            current_end = client_service.start_date or date.today()
        
        new_start = current_end + timedelta(days=1)
        new_end = ServicePeriodManager._calculate_end_date(new_start, extension_months)
        
        return ServicePeriodManager.extend_service_to_date(
            client_service=client_service,
            new_end_date=new_end,
            notes=notes
        )
    
    @staticmethod
    def get_pending_periods(client_service: ClientService) -> List[ServicePayment]:
        return client_service.payments.filter(
            status__in=[
                ServicePayment.StatusChoices.PERIOD_CREATED,
                ServicePayment.StatusChoices.PENDING
            ]
        ).order_by('period_start')
    
    @staticmethod
    def get_last_period(client_service: ClientService) -> ServicePayment:
        return client_service.payments.order_by('-period_end').first()
    
    @staticmethod
    def get_unpaid_periods_summary(client_service: ClientService) -> Dict[str, Any]:
        pending_periods = ServicePeriodManager.get_pending_periods(client_service)
        
        total_days = sum(period.duration_days for period in pending_periods)
        total_months = total_days / 30
        total_amount = sum(period.amount for period in pending_periods)
        
        return {
            'periods': pending_periods,
            'count': pending_periods.count(),
            'total_days': total_days,
            'total_months': round(total_months, 1),
            'total_amount': total_amount,
            'earliest_start': pending_periods.first().period_start if pending_periods else None,
            'latest_end': pending_periods.last().period_end if pending_periods else None
        }
    
    @staticmethod
    def _calculate_end_date(start_date: date, months: int) -> date:
        return start_date + timedelta(days=months * 30 - 1)
    
    @staticmethod
    def _has_overlapping_periods(
        client_service: ClientService,
        start_date: date,
        end_date: date,
        exclude_period_id: Optional[int] = None
    ) -> bool:
        queryset = client_service.payments.filter(
            period_start__lte=end_date,
            period_end__gte=start_date
        )
        
        if exclude_period_id:
            queryset = queryset.exclude(id=exclude_period_id)
        
        return queryset.exists()
