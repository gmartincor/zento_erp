from typing import Dict, Any
from apps.accounting.models import ServicePayment


class StatusDisplayService:
    
    PAYMENT_STATUS_LABELS = {
        'AWAITING_START': 'Pendiente de pago',
        'UNPAID_ACTIVE': 'Sin pagar',
        'PAID': 'Pagado',
        'OVERDUE': 'Vencido',
        'REFUNDED': 'Reembolsado'
    }
    
    PAYMENT_STATUS_CLASSES = {
        'AWAITING_START': 'bg-blue-100 text-blue-800',
        'UNPAID_ACTIVE': 'bg-orange-100 text-orange-800',
        'PAID': 'bg-green-100 text-green-800',
        'OVERDUE': 'bg-red-100 text-red-800',
        'REFUNDED': 'bg-purple-100 text-purple-800'
    }
    
    SERVICE_STATUS_LABELS = {
        'active': 'Activo',
        'no_periods': 'Sin períodos',
        'renewal_due': 'Renovar pronto',
        'expiring_soon': 'Vence pronto',
        'expired': 'Vencido',
        'inactive': 'Pausado',
        'suspended': 'Suspendido'
    }
    
    SERVICE_STATUS_CLASSES = {
        'active': 'bg-green-100 text-green-800',
        'no_periods': 'bg-slate-100 text-slate-800',
        'renewal_due': 'bg-yellow-100 text-yellow-800',
        'expiring_soon': 'bg-orange-100 text-orange-800',
        'expired': 'bg-red-100 text-red-800',
        'inactive': 'bg-gray-100 text-gray-800',
        'suspended': 'bg-red-100 text-red-800'
    }
    
    @classmethod
    def get_payment_status_display(cls, status: str) -> Dict[str, str]:
        return {
            'label': cls.PAYMENT_STATUS_LABELS.get(status, status),
            'class': cls.PAYMENT_STATUS_CLASSES.get(status, 'bg-gray-100 text-gray-800')
        }
    
    @classmethod
    def get_service_status_display(cls, status: str, days_left: int = None) -> Dict[str, str]:
        label = cls.SERVICE_STATUS_LABELS.get(status, status)
        
        if status == 'renewal_due' and days_left is not None:
            label = f'Renovar en {days_left} días' if days_left > 0 else 'Renovar pronto'
        elif status == 'expiring_soon' and days_left is not None:
            if days_left > 0:
                label = f'Vence en {days_left} días'
            else:
                label = 'Vencido hoy'
        elif status == 'expired' and days_left is not None:
            if days_left < 0:
                label = f'Vencido hace {abs(days_left)} días'
            else:
                label = 'Vencido'
        
        return {
            'label': label,
            'class': cls.SERVICE_STATUS_CLASSES.get(status, 'bg-gray-100 text-gray-800')
        }
