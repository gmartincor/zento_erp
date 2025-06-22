from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from apps.accounting.services.presentation_service import PresentationService

register = template.Library()


@register.simple_tag
def business_line_styling(business_line, style_type='bg_class'):
    service = PresentationService()
    styling = service.business_line.get_level_styling(business_line)
    return styling.get(style_type, '')


@register.simple_tag
def status_badge(business_line):
    service = PresentationService()
    badge = service.business_line.get_status_badge(business_line)
    return format_html(
        '<span class="px-2 py-1 text-xs font-semibold rounded-full {}">{}</span>',
        badge['class'],
        badge['text']
    )


@register.simple_tag
def level_badge(business_line):
    service = PresentationService()
    badge = service.business_line.get_level_badge(business_line)
    return format_html(
        '<span class="px-2 py-1 text-xs font-semibold rounded-full {}">{}</span>',
        badge['class'],
        badge['text']
    )


@register.simple_tag
def category_badge(category_code):
    service = PresentationService()
    badge = service.category.get_category_badge(category_code)
    return format_html(
        '<span class="px-3 py-1 text-sm font-medium rounded-full {}">{}</span>',
        badge['class'],
        badge['text']
    )


@register.filter
def format_currency(amount, currency='€'):
    service = PresentationService()
    return service.financial.format_currency(amount, currency)


@register.filter
def format_percentage(value, decimals=1):
    service = PresentationService()
    return service.financial.format_percentage(value, decimals)


@register.filter
def format_count(count, text):
    service = PresentationService()
    return service.financial.format_count(count, text)


@register.simple_tag
def user_can_edit(user, business_line):
    service = PresentationService()
    return service.permissions.can_edit_business_line(user, business_line)


@register.simple_tag
def user_can_view_advanced(user):
    service = PresentationService()
    return service.permissions.can_view_advanced_stats(user)


@register.inclusion_tag('accounting/components/user_actions.html')
def render_user_actions(user, business_line):
    service = PresentationService()
    actions = service.permissions.get_user_actions(user, business_line)
    return {
        'actions': actions,
        'user': user,
        'business_line': business_line
    }


@register.simple_tag
def calculate_percentage(part, total):
    service = PresentationService()
    return service.financial.calculate_percentage(part, total)


@register.inclusion_tag('accounting/components/business_line_card.html')
def business_line_card(business_line, user=None, show_actions=True):
    service = PresentationService()
    presentation_data = service.prepare_business_line_presentation(business_line, user)
    return {
        'business_line': business_line,
        'presentation': presentation_data,
        'show_actions': show_actions,
        'user': user
    }


@register.inclusion_tag('accounting/components/level_icon.html')
def level_icon(business_line, size='w-8 h-8'):
    service = PresentationService()
    styling = service.business_line.get_level_styling(business_line)
    return {
        'icon_type': styling['icon'],
        'css_class': styling['text_class'],
        'size': size
    }


@register.inclusion_tag('accounting/components/admin_actions.html')
def admin_action_buttons(user, business_line, line_path):
    return {
        'user': user,
        'business_line': business_line,
        'line_path': line_path
    }
