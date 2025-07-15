from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from apps.core.constants import SERVICE_CATEGORIES, CATEGORY_CONFIG
from datetime import date, timedelta
from apps.business_lines.models import BusinessLine
from ..models import ServicePayment
from ..services.revenue_analytics_service import RevenueAnalyticsService


def _get_period_filters_and_range(period):
    today = timezone.now().date()
    analytics_service = RevenueAnalyticsService()

    if period == 'current_month':
        return {'year': today.year, 'month': today.month, 'date_range': None}
    elif period == 'current_year':
        return {'year': today.year, 'month': None, 'date_range': None}
    elif period == 'last_year':
        return {'year': today.year - 1, 'month': None, 'date_range': None}
    else:
        period_dates = analytics_service._get_period_dates(period)
        if period_dates:
            return {'year': None, 'month': None, 'date_range': period_dates}
        return {'year': None, 'month': None, 'date_range': None}


@login_required
def revenue_summary_view(request, category=SERVICE_CATEGORIES['PERSONAL']):
    search = request.GET.get('search', '').strip()
    business_line_id = request.GET.get('business_line')
    payment_method = request.GET.get('payment_method')
    period = request.GET.get('period', 'current_month')
    
    if business_line_id:
        try:
            business_line_id = int(business_line_id)
        except (ValueError, TypeError):
            business_line_id = None

    period_filters = _get_period_filters_and_range(period)
    year = period_filters['year']
    month = period_filters['month']
    date_range = period_filters['date_range']

    business_lines_choices = []
    for line in BusinessLine.objects.filter(is_active=True).order_by('name'):
        level_prefix = "  " * line.level
        business_lines_choices.append((line.id, f"{level_prefix}{line.name}"))

    context = {
        'category': category,
        'category_display': CATEGORY_CONFIG[category]['name'],
        'page_title': f'Ingresos - Categoría {category.title()}',
        'page_subtitle': f'Análisis de ingresos por líneas de negocio - Categoría {category.title()}',
        'selected_payment_method': payment_method,
        'search': search,
        'selected_business_line': business_line_id,
        'business_lines_choices': business_lines_choices,
        'payment_methods': ServicePayment.PaymentMethodChoices.choices,
        'period': period,
        'available_periods': [
            ('current_month', 'Mes actual'),
            ('last_month', 'Mes anterior'),
            ('current_year', 'Año actual'),
            ('last_year', 'Año anterior'),
            ('last_3_months', 'Últimos 3 meses'),
            ('last_6_months', 'Últimos 6 meses'),
            ('last_12_months', 'Últimos 12 meses'),
            ('all_time', 'Histórico total'),
        ]
    }
    
    root_lines = BusinessLine.objects.filter(parent__isnull=True, is_active=True).order_by('name')
    
    if business_line_id:
        try:
            selected_line = BusinessLine.objects.get(id=business_line_id, is_active=True)
            if selected_line.parent is None:
                root_lines = [selected_line]
            else:
                root_lines = [selected_line]
        except BusinessLine.DoesNotExist:
            pass
    
    if search:
        root_lines = root_lines.filter(
            Q(name__icontains=search) | 
            Q(client_services__client__full_name__icontains=search)
        ).distinct()
    
    lines_data = []
    
    def build_line_data(line, level=0, force_include=False):
        stats = calculate_revenue_stats_filtered(
            business_line=line, category=category, year=year, month=month, payment_method=payment_method, date_range=date_range
        )
        
        should_include = force_include
        if search and not force_include:
            line_matches = search.lower() in line.name.lower()
            service_matches = line.client_services.filter(
                client__full_name__icontains=search
            ).exists()
            should_include = line_matches or service_matches
        elif not search:
            should_include = True
        
        children_data = []
        if business_line_id:
            if line.id == business_line_id:
                for child in line.children.filter(is_active=True).order_by('name'):
                    child_data = build_line_data(child, level + 1, force_include=True)
                    if child_data:
                        children_data.append(child_data)
        else:
            for child in line.children.filter(is_active=True).order_by('name'):
                child_data = build_line_data(child, level + 1)
                if child_data:
                    children_data.append(child_data)
        
        if should_include or children_data:
            return {
                'line': line,
                'level': level,
                'stats': stats,
                'children': children_data
            }
        return None
    
    for root_line in root_lines:
        line_data = build_line_data(root_line)
        if line_data:
            lines_data.append(line_data)
    
    if business_line_id:
        try:
            selected_line = BusinessLine.objects.get(id=business_line_id, is_active=True)
            stats = calculate_revenue_stats_filtered(
                business_line=selected_line, category=category, year=year, month=month, payment_method=payment_method, date_range=date_range
            )
            total_summary = {
                'total_amount': stats['total_amount'],
                'total_payments': stats['total_payments'],
                'average_amount': stats['average_amount']
            }
        except BusinessLine.DoesNotExist:
            stats = calculate_revenue_stats_filtered(category=category, year=year, month=month, payment_method=payment_method, date_range=date_range)
            total_summary = {
                'total_amount': stats['total_amount'],
                'total_payments': stats['total_payments'],
                'average_amount': stats['average_amount']
            }
    else:
        total_amount = Decimal('0')
        total_payments = 0
        
        for line_data in lines_data:
            total_amount += line_data['stats']['total_amount']
            total_payments += line_data['stats']['total_payments']
        
        total_summary = {
            'total_amount': total_amount,
            'total_payments': total_payments,
            'average_amount': total_amount / total_payments if total_payments > 0 else Decimal('0')
        }
    
    context['total_summary'] = total_summary
    context['revenue_data'] = lines_data
    
    return render(request, 'accounting/revenue_summary.html', context)


def get_all_descendant_lines(business_line):
    descendants = [business_line]
    for child in business_line.children.filter(is_active=True):
        descendants.extend(get_all_descendant_lines(child))
    return descendants

def calculate_revenue_stats_filtered(business_line=None, category=SERVICE_CATEGORIES['PERSONAL'], year=None, month=None, payment_method=None, date_range=None):
    from ..services.payment_service import PaymentService
    
    if business_line:
        all_lines = get_all_descendant_lines(business_line)
        services = []
        for line in all_lines:
            services.extend(line.client_services.filter(category=category))
        
        if services:
            payments = ServicePayment.objects.filter(
                client_service__in=services,
                status__in=[ServicePayment.StatusChoices.PAID, ServicePayment.StatusChoices.REFUNDED],
                amount__isnull=False
            )
        else:
            payments = ServicePayment.objects.none()
    else:
        payments = ServicePayment.objects.filter(
            client_service__category=category,
            status__in=[ServicePayment.StatusChoices.PAID, ServicePayment.StatusChoices.REFUNDED],
            amount__isnull=False
        )
    
    # Aplicar filtros de fecha
    if date_range:
        start_date, end_date = date_range
        payments = payments.filter(payment_date__range=[start_date, end_date])
    else:
        if year:
            payments = payments.filter(payment_date__year=year)
        if month:
            payments = payments.filter(payment_date__month=month)
    
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    return PaymentService.calculate_revenue_stats(payments)
