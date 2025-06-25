from django import template
from django.utils.safestring import mark_safe
from apps.accounting.models import ServicePayment

register = template.Library()


@register.filter
def payment_status_badge(status):
    """Genera un badge HTML para el estado del pago"""
    status_classes = {
        'PAID': 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
        'PENDING': 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200',
        'OVERDUE': 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
        'CANCELLED': 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200',
        'REFUNDED': 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200'
    }
    
    status_labels = {
        'PAID': 'Pagado',
        'PENDING': 'Pendiente',
        'OVERDUE': 'Vencido',
        'CANCELLED': 'Cancelado',
        'REFUNDED': 'Reembolsado'
    }
    
    css_class = status_classes.get(status, status_classes['PENDING'])
    label = status_labels.get(status, status)
    
    return mark_safe(
        f'<span class="px-2 py-1 {css_class} text-xs rounded-full">{label}</span>'
    )


@register.filter
def service_status_badge(status):
    """Genera un badge HTML para el estado del servicio"""
    status_classes = {
        'ACTIVE': 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
        'EXPIRED': 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
        'INACTIVE': 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200',
        'SUSPENDED': 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200'
    }
    
    status_labels = {
        'ACTIVE': 'Activo',
        'EXPIRED': 'Expirado',
        'INACTIVE': 'Inactivo',
        'SUSPENDED': 'Suspendido'
    }
    
    css_class = status_classes.get(status, status_classes['INACTIVE'])
    label = status_labels.get(status, status)
    
    return mark_safe(
        f'<span class="px-2 py-1 {css_class} text-xs rounded-full">{label}</span>'
    )


@register.filter
def payment_method_display(method):
    """Convierte el método de pago a su representación legible"""
    if not method:
        return "No definido"
    
    method_choices = dict(ServicePayment.PaymentMethodChoices.choices)
    return method_choices.get(method, method)


@register.filter
def currency_format(amount):
    """Formatea un monto como moneda"""
    if amount is None:
        return "0,00€"
    
    try:
        return f"{float(amount):,.2f}€".replace(',', '.')
    except (ValueError, TypeError):
        return "0,00€"


@register.inclusion_tag('accounting/components/service_status_indicator.html')
def service_status_indicator(service):
    """Muestra un indicador visual del estado del servicio"""
    return {
        'service': service,
        'status': service.current_status,
        'active_until': service.active_until
    }


@register.inclusion_tag('accounting/components/payment_info_card.html')
def payment_info_card(service):
    """Muestra una tarjeta con información de pagos del servicio"""
    return {
        'service': service,
        'has_payments': service.payment_count > 0,
        'current_amount': service.current_amount,
        'payment_method': service.current_payment_method,
        'payment_method_display': service.get_payment_method_display(),
        'start_date': service.current_start_date,
        'end_date': service.current_end_date
    }
