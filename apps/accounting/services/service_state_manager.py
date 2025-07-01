from typing import Dict, Any, Optional
from datetime import date, timedelta
from django.utils import timezone
from ..models import ClientService, ServicePayment
from .date_calculator import DateCalculator


class ServiceStateManager:
    
    RENEWAL_WARNING_DAYS = 15
    EXPIRING_SOON_DAYS = 7
    
    @classmethod
    def is_service_active(cls, service) -> bool:
        cls._auto_deactivate_if_scheduled(service)
        
        if not service.is_active:
            return False
        
        if service.admin_status == 'SUSPENDED':
            return False
        
        last_period = cls._get_last_period(service)
        if last_period:
            return not DateCalculator.is_date_in_past(last_period.period_end)
        
        return True
    
    @classmethod
    def is_service_expired(cls, service: ClientService) -> bool:
        cls._auto_deactivate_if_scheduled(service)
        
        if not service.is_active:
            return True
        
        last_period = cls._get_last_period(service)
        if last_period:
            return DateCalculator.is_date_in_past(last_period.period_end)
        
        return False
    
    @classmethod
    def days_until_expiry(cls, service: ClientService) -> int:
        last_period = cls._get_last_period(service)
        if last_period:
            return DateCalculator.days_between(DateCalculator.get_today(), last_period.period_end)
        
        return 0
    
    @classmethod
    def get_service_status(cls, service) -> str:
        cls._auto_deactivate_if_scheduled(service)
        
        if not service.is_active:
            return 'inactive'
        
        if service.admin_status == 'SUSPENDED':
            return 'suspended'
        
        last_period = cls._get_last_period(service)
        has_pending_periods = service.payments.filter(
            status__in=['PERIOD_CREATED', 'PENDING']
        ).exists()
        
        if not last_period:
            return 'no_periods'
        
        if has_pending_periods:
            has_paid_periods = service.payments.filter(status=ServicePayment.StatusChoices.PAID).exists()
            if has_paid_periods:
                if cls.is_service_expired(service):
                    return 'expired'
                else:
                    return 'active'
            else:
                return 'pending_payment'
        
        if cls.is_service_expired(service):
            return 'expired'
        
        days_left = cls.days_until_expiry(service)
        if days_left <= cls.EXPIRING_SOON_DAYS:
            return 'expiring_soon'
        elif days_left <= cls.RENEWAL_WARNING_DAYS:
            return 'renewal_due'
        else:
            return 'active'
    
    @classmethod
    def _get_last_period(cls, service: ClientService) -> Optional[ServicePayment]:
        return service.payments.order_by('-period_end').first()
    
    @classmethod
    def get_status_display_data(cls, service: ClientService) -> Dict[str, Any]:
        status = cls.get_service_status(service)
        days_left = cls.days_until_expiry(service)
        
        status_map = {
            'active': {
                'label': 'Activo',
                'class': 'badge-success',
                'icon': 'check-circle',
                'color': 'green'
            },
            'no_periods': {
                'label': 'Sin períodos',
                'class': 'badge-warning',
                'icon': 'calendar-plus',
                'color': 'yellow'
            },
            'pending_payment': {
                'label': 'Pago pendiente',
                'class': 'badge-info',
                'icon': 'credit-card',
                'color': 'blue'
            },
            'renewal_due': {
                'label': f'Renovar en {days_left} días' if days_left > 0 else 'Renovar pronto',
                'class': 'badge-warning',
                'icon': 'exclamation-triangle',
                'color': 'yellow'
            },
            'expiring_soon': {
                'label': cls._get_expiring_label(days_left),
                'class': 'badge-danger',
                'icon': 'clock',
                'color': 'orange'
            },
            'expired': {
                'label': cls._get_expired_label(days_left),
                'class': 'badge-danger',
                'icon': 'x-circle',
                'color': 'red'
            },
            'inactive': {
                'label': 'Pausado',
                'class': 'badge-secondary',
                'icon': 'pause-circle',
                'color': 'gray'
            },
            'suspended': {
                'label': 'Suspendido',
                'class': 'badge-warning',
                'icon': 'ban',
                'color': 'orange'
            }
        }
        
        base_data = status_map.get(status, status_map['inactive'])
        base_data.update({
            'status': status,
            'days_left': days_left
        })
        
        return base_data
    
    @classmethod
    def _get_expiring_label(cls, days_left: int) -> str:
        if days_left == 0:
            return 'Vence hoy'
        elif days_left == 1:
            return 'Vence mañana'
        elif days_left > 0:
            return f'Vence en {days_left} días'
        else:
            return cls._get_expired_label(days_left)
    
    @classmethod
    def _get_expired_label(cls, days_left: int) -> str:
        if days_left == 0:
            return 'Vence hoy'
        elif days_left < 0:
            return f'Vencido {DateCalculator.format_days_difference(days_left)}'
        else:
            return 'Vencido'
    
    @classmethod
    def get_status_display(cls, status: str) -> str:
        status_labels = {
            'active': 'Activo',
            'no_periods': 'Sin Períodos',
            'pending_payment': 'Pago Pendiente',
            'renewal_due': 'Renovar Pronto',
            'expiring_soon': 'Vence Pronto',
            'expired': 'Vencido',
            'inactive': 'Pausado',
            'suspended': 'Suspendido'
        }
        return status_labels.get(status, 'Desconocido')
    
    @classmethod
    def get_status_priority(cls, status: str) -> int:
        priorities = {
            'expired': 1,
            'expiring_soon': 2,
            'renewal_due': 3,
            'pending_payment': 4,
            'no_periods': 5,
            'suspended': 6,
            'inactive': 7,
            'active': 8,
        }
        return priorities.get(status, 0)
    
    @classmethod
    def get_service_summary(cls, service: ClientService) -> Dict[str, Any]:
        status = cls.get_service_status(service)
        days_left = cls.days_until_expiry(service)
        
        return {
            'status': status,
            'status_display': cls.get_status_display(status),
            'is_active': cls.is_service_active(service),
            'is_expired': cls.is_service_expired(service),
            'needs_renewal': cls.needs_renewal(service),
            'days_left': days_left,
            'priority': cls.get_status_priority(status)
        }
    
    @classmethod
    def needs_renewal(cls, service: ClientService) -> bool:
        if not service.is_active:
            return False
        
        status = cls.get_service_status(service)
        return status in ['renewal_due', 'expiring_soon', 'expired']
    
    @classmethod
    def _auto_deactivate_if_scheduled(cls, service):
        from django.db import transaction
        
        if service.is_active and service.end_date:
            today = DateCalculator.get_today()
            # El servicio se desactiva al día siguiente de su fecha de finalización
            if service.end_date < today:
                with transaction.atomic():
                    service.is_active = False
                    service.save(update_fields=['is_active', 'modified'])
    
    @classmethod
    def get_service_detailed_info(cls, service: ClientService) -> Dict[str, Any]:
        status = cls.get_service_status(service)
        
        pending_periods = service.payments.filter(
            status__in=[ServicePayment.StatusChoices.PERIOD_CREATED, ServicePayment.StatusChoices.PENDING]
        ).order_by('period_start')
        
        paid_periods = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-period_end')
        
        last_period = cls._get_last_period(service)
        last_paid_period = paid_periods.first() if paid_periods.exists() else None
        
        return {
            'status': status,
            'pending_periods': pending_periods,
            'paid_periods': paid_periods,
            'last_period': last_period,
            'last_paid_period': last_paid_period,
            'total_vigency_until': last_period.period_end if last_period else None,
            'paid_vigency_until': last_paid_period.period_end if last_paid_period else None,
            'has_mixed_periods': pending_periods.exists() and paid_periods.exists()
        }
