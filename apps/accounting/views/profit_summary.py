from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum, F
from decimal import Decimal
from apps.core.constants import SERVICE_CATEGORIES, CATEGORY_CONFIG
from datetime import date, timedelta
from apps.expenses.models import Expense
from ..models import ServicePayment, ClientService
from ..services.payment_service import PaymentService
from ..services.revenue_analytics_service import RevenueAnalyticsService


def _get_period_filters_and_range(period):

    today = timezone.now().date()
    analytics_service = RevenueAnalyticsService()
    
    # Para períodos simples que pueden usar year/month
    if period == 'current_month':
        return {'year': today.year, 'month': today.month, 'date_range': None}
    elif period == 'current_year':
        return {'year': today.year, 'month': None, 'date_range': None}
    elif period == 'last_year':
        return {'year': today.year - 1, 'month': None, 'date_range': None}
    else:
        # Para todos los demás períodos (incluyendo last_month), usar rangos de fechas
        # para garantizar precisión en el cálculo
        period_dates = analytics_service._get_period_dates(period)
        if period_dates:
            return {'year': None, 'month': None, 'date_range': period_dates}
        return {'year': None, 'month': None, 'date_range': None}


@login_required
def profit_summary_view(request, category=SERVICE_CATEGORIES['PERSONAL']):
    period = request.GET.get('period', 'current_month')
    
    period_filters = _get_period_filters_and_range(period)
    year = period_filters['year']
    month = period_filters['month']
    date_range = period_filters['date_range']

    context = {
        'category': category,
        'category_display': CATEGORY_CONFIG[category]['name'],
        'page_title': f'Beneficios - Categoría {category.title()}',
        'page_subtitle': f'Análisis de beneficios por categoría - {category.title()}',
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
    
    profit_data = calculate_profit_for_category(category, year, month, date_range)
    context.update(profit_data)
    
    return render(request, 'accounting/profit_summary.html', context)


def calculate_profit_for_category(category, year=None, month=None, date_range=None):
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
    
    revenue_stats = PaymentService.calculate_revenue_stats(payments)
    total_revenue = revenue_stats['total_amount']
    
    # Filtros para gastos
    expenses_filter = Q()
    if date_range:
        start_date, end_date = date_range
        expenses_filter &= Q(date__range=[start_date, end_date])
    else:
        if year:
            expenses_filter &= Q(accounting_year=year)
        if month:
            expenses_filter &= Q(accounting_month=month)
    
    total_expenses = Expense.objects.filter(expenses_filter).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    # Filtros para remanentes
    if category == SERVICE_CATEGORIES['BUSINESS']:
        total_remanentes = ServicePayment.objects.filter(
            client_service__category=category,
            status__in=[ServicePayment.StatusChoices.PAID, ServicePayment.StatusChoices.REFUNDED],
            remanente__isnull=False
        )
        
        if date_range:
            start_date, end_date = date_range
            total_remanentes = total_remanentes.filter(payment_date__range=[start_date, end_date])
        else:
            if year:
                total_remanentes = total_remanentes.filter(payment_date__year=year)
            if month:
                total_remanentes = total_remanentes.filter(payment_date__month=month)
        
        total_remanentes = total_remanentes.aggregate(
            total=Sum('remanente')
        )['total'] or Decimal('0')
    else:
        total_remanentes = Decimal('0')
    
    profit = total_revenue - total_expenses - total_remanentes
    
    return {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'total_remanentes': total_remanentes,
        'profit': profit,
        'revenue_stats': revenue_stats
    }
