from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def tenant_url(context, url_name, *args, **kwargs):
    request = context['request']
    if hasattr(request, 'tenant') and request.tenant:
        tenant_slug = request.tenant.slug
        
        if url_name == 'dashboard:home' or url_name == 'dashboard_home':
            return reverse('tenant_dashboard', args=[tenant_slug])
        elif url_name == 'tenant_logout' or url_name == 'logout':
            return reverse('tenant_logout', args=[tenant_slug])
        elif url_name == 'tenant_login' or url_name == 'login':
            return reverse('tenant_login', args=[tenant_slug])
        else:
            try:
                return reverse(url_name, args=[tenant_slug] + list(args), kwargs=kwargs)
            except NoReverseMatch:
                return reverse(url_name, args=list(args), kwargs=kwargs)
    
    try:
        return reverse(url_name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return url_name

@register.simple_tag(takes_context=True)
def is_active_section(context, app_name):
    request = context['request']
    resolver_match = getattr(request, 'resolver_match', None)
    if resolver_match:
        return resolver_match.app_name == app_name or (
            resolver_match.url_name == 'tenant_dashboard' and app_name == 'dashboard'
        )
    return False
