from django import template
from django.urls import reverse
from django.utils.html import format_html

from apps.accounting.services.statistics_service import StatisticsService
from apps.accounting.services.business_line_service import BusinessLineService
from apps.accounting.services.template_tag_service import TemplateTagService
from apps.core.constants import CATEGORY_CONFIG

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
    white_stats = service.calculate_category_performance('white', [business_line])
    black_stats = service.calculate_category_performance('black', [business_line])
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
    status_config = {
        'PAID': ('bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200', 'Pagado'),
        'AWAITING_START': ('bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200', 'Periodo creado sin pago'),
        'UNPAID_ACTIVE': ('bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200', 'Pendiente de pago'),
        'OVERDUE': ('bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200', 'Vencido'),
        'REFUNDED': ('bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200', 'Reembolsado'),
        'PERIOD_CREATED': ('bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200', 'Período creado')
    }
    
    css_class, display_text = status_config.get(payment.status, ('bg-gray-100 text-gray-800', payment.get_status_display()))
    
    return format_html(
        '<span class="px-2 py-1 text-xs font-medium rounded-full {}">{}</span>',
        css_class,
        display_text
    )
