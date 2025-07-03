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
        'AWAITING_START': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
        'UNPAID_ACTIVE': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
        'PAID': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
        'OVERDUE': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
        'REFUNDED': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
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
        'active': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
        'no_periods': 'bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-200',
        'renewal_pending': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
        'expiring_soon': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
        'expired': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
        'inactive': 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
        'suspended': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    }
    
    @classmethod
    def get_payment_status_display(cls, status: str) -> Dict[str, str]:
        if isinstance(status, list):
            status = str(status)
        return {
            'label': cls.PAYMENT_STATUS_LABELS.get(status, status),
            'class': cls.PAYMENT_STATUS_CLASSES.get(status, 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200')
        }
    
    @classmethod
    def get_service_status_display(cls, status: str, days_left: int = None) -> Dict[str, str]:
        if isinstance(status, list):
            status = str(status)
        label = cls.SERVICE_STATUS_LABELS.get(status, status)
        
        return {
            'label': label,
            'class': cls.SERVICE_STATUS_CLASSES.get(status, 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200')
        }
