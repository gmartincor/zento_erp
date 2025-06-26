from django import template
from django.utils.safestring import mark_safe
from ..services.service_state_manager import ServiceStateManager

register = template.Library()


@register.simple_tag
def service_status_badge(service):
    status_data = ServiceStateManager.get_status_display_data(service)
    
    color_classes = {
        'green': 'bg-green-100 text-green-800 border-green-200',
        'yellow': 'bg-yellow-100 text-yellow-800 border-yellow-200',
        'orange': 'bg-orange-100 text-orange-800 border-orange-200',
        'red': 'bg-red-100 text-red-800 border-red-200',
        'gray': 'bg-gray-100 text-gray-800 border-gray-200',
    }
    
    css_class = color_classes.get(status_data['color'], color_classes['gray'])
    
    return mark_safe(
        f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border {css_class}">'
        f'{status_data["label"]}'
        f'</span>'
    )


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
    
    active_until = status_data.get('active_until')
    if not active_until:
        return "Sin fecha de vencimiento"
    
    days_left = status_data.get('days_left', 0)
    
    if days_left <= 0:
        days_overdue = abs(days_left)
        if days_overdue == 0:
            return "Vence hoy"
        elif days_overdue == 1:
            return "Vencido hace 1 día"
        else:
            return f"Vencido hace {days_overdue} días"
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
