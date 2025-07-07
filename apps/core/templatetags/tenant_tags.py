from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def tenant_url(context, url_name, *args, **kwargs):
    request = context['request']
    if hasattr(request, 'tenant') and request.tenant:
        if url_name == 'dashboard:home':
            return reverse('tenant_dashboard', args=[request.tenant.slug])
        elif url_name.startswith('dashboard:'):
            return f"/{request.tenant.slug}/{url_name.replace('dashboard:', 'dashboard/')}/"
        elif url_name.startswith('accounting:'):
            return f"/{request.tenant.slug}/{url_name.replace('accounting:', 'accounting/')}/"
        elif url_name.startswith('expenses:'):
            return f"/{request.tenant.slug}/{url_name.replace('expenses:', 'expenses/')}/"
        elif url_name == 'tenant_logout':
            return reverse('tenant_logout', args=[request.tenant.slug])
    return reverse(url_name, args=args, kwargs=kwargs)

@register.simple_tag(takes_context=True)
def is_active_section(context, app_name):
    request = context['request']
    resolver_match = getattr(request, 'resolver_match', None)
    if resolver_match:
        return resolver_match.app_name == app_name or (
            resolver_match.url_name == 'tenant_dashboard' and app_name == 'dashboard'
        )
    return False
