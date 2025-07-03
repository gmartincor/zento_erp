from django import template
from django.utils.safestring import mark_safe
from ..services.service_state_manager import ServiceStateManager
from ..services.service_termination_manager import ServiceTerminationManager

register = template.Library()


@register.simple_tag
def service_status_badge(service):
    from ..services.status_display_service import StatusDisplayService
    from ..services.service_state_manager import ServiceStateManager
    
    status = ServiceStateManager.get_service_status(service)
    days_left = ServiceStateManager.days_until_expiry(service)
    status_data = StatusDisplayService.get_service_status_display(status, days_left)
    
    return mark_safe(
        f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {status_data["class"]}">'
        f'{status_data["label"]}'
        f'</span>'
    )


@register.filter
def service_status_badge_filter(service):
    return service_status_badge(service)


@register.simple_tag
def service_status_icon(service):
    status_data = ServiceStateManager.get_status_display_data(service)
    
    icon_paths = {
        'check-circle': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>',
        'x-circle': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path>',
        'pause-circle': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>',
        'exclamation-triangle': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"></path>',
        'clock': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>'
    }
    
    color_classes = {
        'green': 'text-green-500',
        'yellow': 'text-yellow-500',
        'orange': 'text-orange-500',
        'red': 'text-red-500',
        'gray': 'text-gray-500',
    }
    
    icon = status_data.get('icon', 'pause-circle')
    color = status_data.get('color', 'gray')
    
    icon_path = icon_paths.get(icon, icon_paths['pause-circle'])
    icon_class = color_classes.get(color, color_classes['gray'])
    
    return mark_safe(
        f'<svg class="w-5 h-5 {icon_class}" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
        f'{icon_path}'
        f'</svg>'
    )


@register.simple_tag
def service_expiry_info(service):
    status_data = ServiceStateManager.get_status_display_data(service)
    
    if not service.end_date:
        return "Sin fecha de vencimiento"
    
    days_left = status_data.get('days_left', 0)
    
    if days_left < 0:
        days_overdue = abs(days_left)
        if days_overdue == 1:
            return "Vencido hace 1 día"
        else:
            return f"Vencido hace {days_overdue} días"
    elif days_left == 0:
        return "Vence hoy"
    elif days_left == 1:
        return "Vence mañana"
    elif days_left <= 7:
        return f"Vence en {days_left} días"
    elif days_left <= 30:
        return f"Vence en {days_left} días"
    else:
        return f"Activo por {days_left} días más"


@register.filter
def service_needs_renewal(service):
    return ServiceStateManager.needs_renewal(service)


@register.filter
def service_is_active(service):
    return ServiceStateManager.is_service_active(service)


@register.filter
def service_is_expired(service):
    return ServiceStateManager.is_service_expired(service)


@register.simple_tag 
def service_vigency_info(service):
    last_paid_period = service.payments.filter(status='PAID').order_by('-period_end').first()
    paid_end_date = last_paid_period.period_end if last_paid_period else None
    
    has_discrepancy = False
    discrepancy_type = None
    discrepancy_days = 0
    
    if service.end_date and paid_end_date:
        if service.end_date != paid_end_date:
            has_discrepancy = True
            discrepancy_days = abs((service.end_date - paid_end_date).days)
            discrepancy_type = 'early_termination' if service.end_date < paid_end_date else 'late_payment'
    
    return {
        'end_date': service.end_date,
        'paid_end_date': paid_end_date,
        'has_paid_periods': paid_end_date is not None,
        'has_discrepancy': has_discrepancy,
        'discrepancy_type': discrepancy_type,
        'discrepancy_days': discrepancy_days
    }


@register.simple_tag
def service_pending_periods(service):
    return service.payments.filter(
        status__in=['PERIOD_CREATED', 'PENDING']
    ).order_by('period_start')

@register.simple_tag
def service_payment_summary(service):
    pending_periods = service.payments.filter(
        status__in=['PERIOD_CREATED', 'PENDING']
    ).order_by('period_start')
    
    paid_periods = service.payments.filter(
        status='PAID'
    ).order_by('-period_end')
    
    total_paid = sum(p.amount for p in paid_periods if p.amount)
    total_pending = sum(p.amount for p in pending_periods if p.amount)
    
    return {
        'pending_periods': pending_periods,
        'paid_periods': paid_periods,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'paid_count': paid_periods.count(),
        'pending_count': pending_periods.count()
    }


@register.inclusion_tag('accounting/components/service_operational_status_badge.html')
def service_operational_status_badge(service):
    is_active = ServiceStateManager.is_service_active(service)
    
    return {
        'is_active': is_active,
        'label': 'Activo' if is_active else 'Inactivo',
        'css_class': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' if is_active else 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    }


@register.simple_tag
def service_payment_status_badge(service):
    from ..services.status_display_service import StatusDisplayService
    
    latest_payment = service.payments.order_by('-created').first()
    if not latest_payment:
        status_data = StatusDisplayService.get_payment_status_display('AWAITING_START')
    else:
        status_data = StatusDisplayService.get_payment_status_display(latest_payment.status)
    
    return mark_safe(
        f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {status_data["class"]}">'
        f'{status_data["label"]}'
        f'</span>'
    )


@register.simple_tag
def service_renewal_status_badge(service):
    from ..services.service_state_manager import ServiceStateManager
    from ..services.status_display_service import StatusDisplayService
    
    status = ServiceStateManager.get_service_status(service)
    days_left = ServiceStateManager.days_until_expiry(service)
    status_data = StatusDisplayService.get_service_status_display(status, days_left)
    
    return mark_safe(
        f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {status_data["class"]}">'
        f'{status_data["label"]}'
        f'</span>'
    )
