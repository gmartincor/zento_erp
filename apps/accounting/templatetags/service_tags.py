from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def service_status_badge(status):
    """
    DEPRECATED: Usar service_status_badge de service_status_tags que usa StatusDisplayService
    """
    from ..services.status_display_service import StatusDisplayService
    
    status_data = StatusDisplayService.get_service_status_display(status)
    
    return format_html(
        '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">{}</span>',
        status_data['class'], status_data['label']
    )


@register.filter
def currency_format(value):
    try:
        return f"€{float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "€0,00"


@register.filter
def payment_method_display(method):
    method_display = {
        'cash': 'Efectivo',
        'transfer': 'Transferencia',
        'card': 'Tarjeta',
        'bizum': 'Bizum',
        'check': 'Cheque'
    }
    return method_display.get(method, method.title())


@register.filter
def payment_status_badge(status):
    """
    DEPRECATED: Usar payment_status_badge de status_tags que usa StatusDisplayService
    """
    from ..services.status_display_service import StatusDisplayService
    
    status_data = StatusDisplayService.get_payment_status_display(status)
    
    return format_html(
        '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">{}</span>',
        status_data['class'], status_data['label']
    )
