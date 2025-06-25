from typing import Dict, Any
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal

from apps.accounting.models import ClientService, ServicePayment


class ServiceInfoService:
    
    @staticmethod
    def get_service_summary(service: ClientService) -> Dict[str, Any]:
        return {
            'basic_info': ServiceInfoService._get_basic_info(service),
            'payment_info': ServiceInfoService._get_payment_info(service),
            'status_info': ServiceInfoService._get_status_info(service),
            'statistics': ServiceInfoService._get_statistics(service)
        }
    
    @staticmethod
    def _get_basic_info(service: ClientService) -> Dict[str, Any]:
        return {
            'id': service.id,
            'client_name': service.client.full_name,
            'client_dni': service.client.dni,
            'business_line': service.business_line.name,
            'business_line_level': service.business_line.level,
            'category': service.category,
            'category_display': service.get_category_display(),
            'created': service.created,
            'modified': service.modified
        }
    
    @staticmethod
    def _get_payment_info(service: ClientService) -> Dict[str, Any]:
        latest_payment = service.payments.order_by('-created').first()
        
        if not latest_payment:
            return {
                'has_payments': False,
                'current_amount': None,
                'current_payment_method': None,
                'current_start_date': None,
                'current_end_date': None,
                'payment_method_display': 'No definido'
            }
        
        payment_choices = dict(ServicePayment.PaymentMethodChoices.choices)
        
        return {
            'has_payments': True,
            'current_amount': latest_payment.amount,
            'current_payment_method': latest_payment.payment_method,
            'current_start_date': latest_payment.period_start,
            'current_end_date': latest_payment.period_end,
            'payment_method_display': payment_choices.get(
                latest_payment.payment_method, 
                latest_payment.payment_method
            )
        }
    
    @staticmethod
    def _get_status_info(service: ClientService) -> Dict[str, Any]:
        latest_payment = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-period_end').first()
        
        if not latest_payment:
            return {
                'status': 'INACTIVE',
                'status_display': 'Inactivo',
                'active_until': None,
                'is_active': False,
                'days_until_expiry': None
            }
        
        today = timezone.now().date()
        days_until_expiry = (latest_payment.period_end - today).days
        
        if latest_payment.period_end >= today:
            status = 'ACTIVE'
            status_display = 'Activo'
            is_active = True
        elif days_until_expiry >= -30:
            status = 'EXPIRED_RECENT'
            status_display = 'Expirado reciente'
            is_active = False
        else:
            status = 'EXPIRED'
            status_display = 'Expirado'
            is_active = False
        
        return {
            'status': status,
            'status_display': status_display,
            'active_until': latest_payment.period_end,
            'is_active': is_active,
            'days_until_expiry': days_until_expiry
        }
    
    @staticmethod
    def _get_statistics(service: ClientService) -> Dict[str, Any]:
        paid_payments = service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        )
        
        total_paid = paid_payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        return {
            'payment_count': paid_payments.count(),
            'total_paid': total_paid,
            'average_payment': total_paid / paid_payments.count() if paid_payments.count() > 0 else Decimal('0.00')
        }
    
    @staticmethod
    def get_service_context_data(service: ClientService) -> Dict[str, Any]:
        summary = ServiceInfoService.get_service_summary(service)
        
        context = {
            'service': service,
            'service_info': summary['basic_info'],
            'payment_info': summary['payment_info'],
            'status_info': summary['status_info'],
            'statistics': summary['statistics']
        }
        
        context.update({
            'current_amount': summary['payment_info']['current_amount'],
            'current_payment_method': summary['payment_info']['current_payment_method'],
            'current_start_date': summary['payment_info']['current_start_date'],
            'current_end_date': summary['payment_info']['current_end_date'],
            'payment_method_display': summary['payment_info']['payment_method_display'],
            'current_status': summary['status_info']['status'],
            'active_until': summary['status_info']['active_until'],
            'payment_count': summary['statistics']['payment_count'],
            'total_paid': summary['statistics']['total_paid']
        })
        
        return context
