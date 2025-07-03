from typing import List, Dict, Any, Optional
from datetime import date
from django.db import transaction
from django.utils import timezone

from ..models import Client, ClientService


class ClientStateManager:
    
    @classmethod
    @transaction.atomic
    def deactivate_client(cls, client: Client, deactivation_date: Optional[date] = None) -> Dict[str, Any]:
        if deactivation_date is None:
            deactivation_date = timezone.now().date()
        
        active_services = client.services.filter(is_active=True)
        deactivated_services = []
        
        for service in active_services:
            cls._freeze_service(service, deactivation_date)
            deactivated_services.append(service.id)
        
        client.is_active = False
        client.save(update_fields=['is_active', 'modified'])
        
        return {
            'client_id': client.id,
            'deactivated_services': deactivated_services,
            'deactivation_date': deactivation_date,
            'total_services_affected': len(deactivated_services)
        }
    
    @classmethod
    @transaction.atomic
    def reactivate_client(cls, client: Client, reactivation_date: Optional[date] = None) -> Dict[str, Any]:
        if reactivation_date is None:
            reactivation_date = timezone.now().date()
        
        frozen_services = client.services.filter(is_active=False)
        reactivated_services = []
        
        for service in frozen_services:
            cls._unfreeze_service(service, reactivation_date)
            reactivated_services.append(service.id)
        
        client.is_active = True
        client.save(update_fields=['is_active', 'modified'])
        
        return {
            'client_id': client.id,
            'reactivated_services': reactivated_services,
            'reactivation_date': reactivation_date,
            'total_services_affected': len(reactivated_services)
        }
    
    @classmethod
    def _freeze_service(cls, service: ClientService, freeze_date: date) -> None:
        from .period_service import ServicePeriodManager
        
        cls._cancel_pending_periods(service, freeze_date)
        
        service.is_active = False
        service.save(update_fields=['is_active', 'modified'])
    
    @classmethod
    def _unfreeze_service(cls, service: ClientService, unfreeze_date: date) -> None:
        service.is_active = True
        service.end_date = unfreeze_date
        service.save(update_fields=['is_active', 'end_date', 'modified'])
    
    @classmethod
    def _cancel_pending_periods(cls, service: ClientService, cancel_date: date) -> None:
        from ..models import ServicePayment
        
        pending_periods = service.payments.filter(
            status__in=[
                ServicePayment.StatusChoices.AWAITING_START,
                ServicePayment.StatusChoices.UNPAID_ACTIVE,
                ServicePayment.StatusChoices.OVERDUE
            ],
            period_start__gte=cancel_date
        )
        
        pending_periods.delete()
        
        last_paid_period = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-period_end').first()
        
        if last_paid_period:
            service.end_date = min(last_paid_period.period_end, cancel_date)
        else:
            service.end_date = cancel_date
        
        service.save(update_fields=['end_date', 'modified'])
    
    @classmethod
    def get_client_services_summary(cls, client: Client) -> Dict[str, Any]:
        services = client.services.all()
        
        return {
            'total_services': services.count(),
            'active_services': services.filter(is_active=True).count(),
            'inactive_services': services.filter(is_active=False).count(),
            'client_active': client.is_active
        }
