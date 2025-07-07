from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe
from django_tenants.utils import connection

register = template.Library()


@register.simple_tag(takes_context=True)
def tenant_url(context, url_name, *args, **kwargs):
    try:
        return reverse(url_name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return url_name


@register.simple_tag(takes_context=True)
def is_active_section(context, app_name):
    """Determina si una sección está activa basándose en la app actual"""
    request = context['request']
    resolver_match = getattr(request, 'resolver_match', None)
    if resolver_match:
        return resolver_match.app_name == app_name or (
            resolver_match.url_name == 'tenant_dashboard' and app_name == 'dashboard'
        )
    return False


@register.simple_tag
def get_current_tenant():
    """Obtiene el tenant actual usando django-tenants"""
    try:
        return connection.tenant
    except:
        return None


@register.filter
def tenant_name(tenant):
    """Filtro para obtener el nombre del tenant de forma segura"""
    return tenant.name if tenant else "Sin tenant"


@register.inclusion_tag('components/tenant_info.html', takes_context=True)
def tenant_info(context):
    """Componente para mostrar información del tenant actual"""
    tenant = get_current_tenant()
    return {
        'tenant': tenant,
        'request': context['request']
    }
