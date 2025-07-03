from typing import Dict, Any
from apps.accounting.models import ServicePayment


class StatusDisplayService:
    
    PAYMENT_STATUS_LABELS = {
        'AWAITING_START': 'Periodo creado sin pago',
        'UNPAID_ACTIVE': 'Pendiente de pago',
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
        'active': 'Al día',
        'no_periods': 'Sin períodos',
        'renewal_pending': 'Pendiente de renovación',
        'expiring_soon': 'Vence pronto',
        'expired': 'Vencido',
        'inactive': 'Pausado',
        'suspended': 'Suspendido'
    }
    
    SERVICE_STATUS_CLASSES = {
        'active': 'bg-green-100 text-green-800',
        'no_periods': 'bg-slate-100 text-slate-800',
        'renewal_pending': 'bg-yellow-100 text-yellow-800',
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
        
        return {
            'label': label,
            'class': cls.SERVICE_STATUS_CLASSES.get(status, 'bg-gray-100 text-gray-800')
        }
