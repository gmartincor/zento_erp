import re
from django import template
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.accounting.services.statistics_service import StatisticsService
from apps.accounting.services.business_line_service import BusinessLineService
from apps.accounting.services.template_tag_service import TemplateTagService
from apps.core.constants import CATEGORY_CONFIG, SERVICE_CATEGORIES

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
    normalized_category = TemplateTagService.normalize_category(category)
    return CATEGORY_CONFIG[normalized_category]['badge_class']

@register.filter
def payment_method_icon(method):
    return TemplateTagService.get_payment_method_icon(method)

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
    personal_stats = service.calculate_category_performance(SERVICE_CATEGORIES['PERSONAL'], [business_line])
    business_stats = service.calculate_category_performance(SERVICE_CATEGORIES['BUSINESS'], [business_line])
    return {
        'business_line': business_line,
        'current_category': current_category,
        'line_path': line_path,
        'personal_count': personal_stats.get('total_services', 0),
        'business_count': business_stats.get('total_services', 0),
        'personal_url': reverse('accounting:category-services', 
                           kwargs={'line_path': line_path, 'category': SERVICE_CATEGORIES['PERSONAL']}),
        'business_url': reverse('accounting:category-services', 
                           kwargs={'line_path': line_path, 'category': SERVICE_CATEGORIES['BUSINESS']})
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
        'url': reverse('accounting:index'),
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
        'category': TemplateTagService.normalize_category(category)
    })
    return reverse(url_name, kwargs=kwargs)

@register.simple_tag
def calculate_remanente_total(service):
    return TemplateTagService.calculate_remanente_total(service)

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
    return TemplateTagService.calculate_percentage(part, total)

@register.simple_tag
def get_client_status(client):
    return TemplateTagService.get_client_reactivation_status(client)

@register.simple_tag
def should_show_reactivation_option(client):
    return TemplateTagService.should_show_reactivation_option(client)

@register.simple_tag
def get_reactivation_url(service, business_line=None, category=None):
    return TemplateTagService.build_reactivation_url(service, business_line, category)

@register.simple_tag
def get_remanente_stats(business_line=None, client_service=None):
    service = StatisticsService()
    return service.calculate_remanente_stats(business_line=business_line, client_service=client_service)

@register.simple_tag
def get_service_remanentes_summary(client_service):
    service = StatisticsService()
    return service.get_service_remanente_summary(client_service)

@register.filter
def remanente_badge_class(has_remanentes):
    if has_remanentes:
        return "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100"
    return "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"

@register.filter
def dict_get(dictionary, key):
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None

@register.filter
def startswith(value, prefix):
    return str(value).startswith(str(prefix))

@register.filter
def add_string(value, string):
    return str(value) + str(string)

@register.filter
def has_fields_starting_with(form_fields, prefix):
    for field_name in form_fields.keys():
        if field_name.startswith(prefix):
            return True
    return False

@register.filter
def split(value, delimiter):
    return str(value).split(str(delimiter))

@register.filter
def get_item(list_value, index):
    try:
        return list_value[int(index)]
    except (IndexError, ValueError, TypeError):
        return ""

@register.simple_tag
def get_service_edit_url(service):
    return TemplateTagService.build_service_edit_url(service)

@register.simple_tag
def get_service_termination_url(service):
    return TemplateTagService.build_service_termination_url(service)

@register.inclusion_tag('accounting/components/payment_amount_display.html')
def payment_amount_display(payment, show_details=True):
    return {
        'payment': payment,
        'show_details': show_details,
        'has_refund': payment.refunded_amount and payment.refunded_amount > 0,
        'original_amount': payment.amount,
        'refunded_amount': payment.refunded_amount or 0,
        'net_amount': payment.net_amount
    }

@register.filter
def payment_status_badge(payment):
    """
    DEPRECATED: Usar payment_status_badge de status_tags que usa StatusDisplayService
    """
    from ..services.status_display_service import StatusDisplayService
    
    status_data = StatusDisplayService.get_payment_status_display(payment.status)
    
    return format_html(
        '<span class="px-2 py-1 text-xs font-medium rounded-full {}">{}</span>',
        status_data['class'],
        status_data['label']
    )

@register.simple_tag
def currency_field(field, symbol='€'):
    field_html = str(field)
    
    # Apply consistent styling to the field without currency symbol
    if 'class="' in field_html:
        field_html = re.sub(
            r'class="[^"]*"',
            'class="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400"',
            field_html
        )
    else:
        field_html = field_html.replace(
            '>',
            ' class="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400">',
            1
        )
    
    # Force placeholder to use dot notation regardless of locale
    if 'placeholder=' not in field_html:
        field_html = field_html.replace('>', ' placeholder="0.00">', 1)
    else:
        field_html = re.sub(r'placeholder="[^"]*"', 'placeholder="0.00"', field_html)
    
    # Force value format to use dot notation
    if 'value=' in field_html:
        field_html = re.sub(r'value="([0-9]+),([0-9]+)"', r'value="\1.\2"', field_html)
    
    return mark_safe(field_html)
