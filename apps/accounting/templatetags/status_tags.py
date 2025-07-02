from django import template
from apps.accounting.services.status_display_service import StatusDisplayService

register = template.Library()


@register.inclusion_tag('accounting/components/dynamic_status_badge.html')
def payment_status_badge(payment):
    status_data = StatusDisplayService.get_payment_status_display(payment.status)
    return {
        'label': status_data['label'],
        'class': status_data['class']
    }


@register.simple_tag
def payment_status_label(status):
    return StatusDisplayService.get_payment_status_display(status)['label']


@register.simple_tag
def service_status_label(status, days_left=None):
    return StatusDisplayService.get_service_status_display(status, days_left)['label']
