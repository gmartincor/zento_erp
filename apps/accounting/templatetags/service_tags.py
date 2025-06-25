from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def service_status_badge(status):
    status_classes = {
        'active': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
        'inactive': 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300',
        'completed': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
        'suspended': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
        'cancelled': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
    }
    
    status_display = {
        'active': 'Activo',
        'inactive': 'Inactivo',
        'completed': 'Completado',
        'suspended': 'Suspendido',
        'cancelled': 'Cancelado'
    }
    
    css_class = status_classes.get(status, status_classes['inactive'])
    display_text = status_display.get(status, status.title())
    
    return format_html(
        '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">{}</span>',
        css_class, display_text
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
    status_classes = {
        'pending': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
        'paid': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
        'overdue': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
        'partial': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
    }
    
    status_display = {
        'pending': 'Pendiente',
        'paid': 'Pagado',
        'overdue': 'Vencido',
        'partial': 'Parcial'
    }
    
    css_class = status_classes.get(status, status_classes['pending'])
    display_text = status_display.get(status, status.title())
    
    return format_html(
        '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">{}</span>',
        css_class, display_text
    )
