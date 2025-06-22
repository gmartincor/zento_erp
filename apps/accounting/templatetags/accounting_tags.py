from decimal import Decimal
from django import template
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils.html import format_html
from django.template.loader import render_to_string

from apps.accounting.models import ClientService
from apps.accounting.services.statistics_service import StatisticsService
from apps.accounting.services.business_line_service import BusinessLineService
from apps.accounting.services.template_service import TemplateDataService

register = template.Library()

@register.simple_tag
def calculate_business_line_stats(business_line, include_children=True):
    service = StatisticsService()
    return service.calculate_business_line_stats(business_line, include_children)

@register.simple_tag
def get_category_performance(category, business_lines):
    service = StatisticsService()
    return service.calculate_category_performance(category, business_lines)

@register.simple_tag
def get_revenue_summary(business_lines, year=None, month=None):
    service = StatisticsService()
    return service.get_revenue_summary_by_period(business_lines, year, month)

@register.simple_tag(takes_context=True)
def get_accessible_business_lines(context):
    user = context['request'].user
    service = BusinessLineService()
    return service.get_accessible_lines(user)

@register.simple_tag(takes_context=True)
def get_root_business_lines(context):
    user = context['request'].user
    service = BusinessLineService()
    return service.get_root_lines_for_user(user)

@register.simple_tag
def build_business_line_path(business_line):
    service = BusinessLineService()
    return service.build_line_path(business_line)

@register.simple_tag
def get_business_line_children(business_line, user_permissions=None):
    service = BusinessLineService()
    return service.get_children_for_display(business_line, user_permissions)

@register.filter
def category_badge_class(category):
    classes = {
        'WHITE': 'bg-blue-100 text-blue-800',
        'BLACK': 'bg-gray-100 text-gray-800'
    }
    return classes.get(category, 'bg-gray-100 text-gray-800')

@register.filter
def payment_method_icon(method):
    icons = {
        'CARD': '💳',
        'CASH': '💵',
        'TRANSFER': '🏦',
        'BIZUM': '📱'
    }
    return icons.get(method, '💰')

@register.inclusion_tag('accounting/components/stats_card.html')
def stats_card(title, value, subtitle=None, icon=None, trend=None):
    return {
        'title': title,
        'value': value,
        'subtitle': subtitle,
        'icon': icon,
        'trend': trend
    }

@register.inclusion_tag('accounting/components/category_tabs.html')
def category_tabs(business_line, current_category, line_path):
    service = StatisticsService()
    white_stats = service.calculate_category_performance('WHITE', [business_line])
    black_stats = service.calculate_category_performance('BLACK', [business_line])
    return {
        'business_line': business_line,
        'current_category': current_category,
        'line_path': line_path,
        'white_count': white_stats.get('total_services', 0),
        'black_count': black_stats.get('total_services', 0),
        'white_url': reverse('accounting:category-services', 
                           kwargs={'line_path': line_path, 'category': 'white'}),
        'black_url': reverse('accounting:category-services', 
                           kwargs={'line_path': line_path, 'category': 'black'})
    }

@register.inclusion_tag('accounting/components/breadcrumb_navigation.html')
def breadcrumb_navigation(business_line, category=None):
    service = BusinessLineService()
    breadcrumbs = []
    current = business_line
    while current:
        path = service.build_line_path(current)
        breadcrumbs.insert(0, {
            'name': current.name,
            'url': reverse('accounting:business-lines-path', kwargs={'line_path': path}),
            'is_current': current == business_line
        })
        current = current.parent
    breadcrumbs.insert(0, {
        'name': 'Dashboard',
        'url': reverse('accounting:dashboard'),
        'is_current': False
    })
    return {
        'breadcrumbs': breadcrumbs,
        'category': category
    }

@register.inclusion_tag('accounting/components/service_summary_table.html')
def service_summary_table(services, show_actions=True):
    return {
        'services': services,
        'show_actions': show_actions
    }

@register.simple_tag
def url_with_category(url_name, line_path, category, **kwargs):
    kwargs.update({
        'line_path': line_path,
        'category': category.lower()
    })
    return reverse(url_name, kwargs=kwargs)

@register.simple_tag
def calculate_remanente_total(service):
    if hasattr(service, 'get_remanente_total'):
        return service.get_remanente_total()
    return 0

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.simple_tag
def format_business_line_hierarchy(business_line):
    indent = "└─ " * (business_line.level - 1)
    return format_html(
        '<span class="text-gray-500">{}</span>{}',
        indent,
        business_line.name
    )

@register.filter
def percentage_of(part, total):
    if not total or total == 0:
        return 0
    try:
        return (float(part) / float(total)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
