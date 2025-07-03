from django import template
from django.http import QueryDict
from urllib.parse import urlencode

register = template.Library()


@register.simple_tag
def build_filter_url(request, **kwargs):
    """
    Construye una URL manteniendo los filtros existentes y agregando/modificando los especificados.
    
    Uso: {% build_filter_url request view='list' operational_status='active' %}
    """
    query_dict = request.GET.copy()
    
    for key, value in kwargs.items():
        if value is None or value == '':
            if key in query_dict:
                del query_dict[key]
        else:
            query_dict[key] = value
    
    if query_dict:
        return '?' + query_dict.urlencode()
    return request.path


@register.simple_tag
def remove_filter_url(request, *filter_names):
    """
    Construye una URL removiendo los filtros especificados.
    
    Uso: {% remove_filter_url request 'operational_status' 'payment_status' %}
    """
    query_dict = request.GET.copy()
    
    for filter_name in filter_names:
        if filter_name in query_dict:
            del query_dict[filter_name]
    
    if query_dict:
        return '?' + query_dict.urlencode()
    return request.path


@register.simple_tag
def preserve_filters_url(request, view_param=None):
    """
    Preserva todos los filtros actuales cambiando solo el parámetro de vista.
    
    Uso: {% preserve_filters_url request 'list' %}
    """
    query_dict = request.GET.copy()
    
    if view_param:
        query_dict['view'] = view_param
    
    if query_dict:
        return '?' + query_dict.urlencode()
    return request.path


@register.filter
def has_any_filter(applied_filters):
    """
    Verifica si hay algún filtro aplicado (excepto vista).
    
    Uso: {{ applied_filters|has_any_filter }}
    """
    filter_keys = ['status', 'operational_status', 'payment_status', 'renewal_status', 'client']
    return any(applied_filters.get(key) for key in filter_keys)


@register.filter 
def get_filter_value(request, filter_name):
    """
    Obtiene el valor de un filtro específico de la request.
    
    Uso: {{ request|get_filter_value:'operational_status' }}
    """
    return request.GET.get(filter_name, '')


@register.inclusion_tag('accounting/components/filter_badge.html')
def filter_badge(label, value, remove_url):
    """
    Renderiza un badge de filtro con opción de remover.
    
    Uso: {% filter_badge 'Estado' 'Activos' remove_url %}
    """
    return {
        'label': label,
        'value': value,
        'remove_url': remove_url
    }
