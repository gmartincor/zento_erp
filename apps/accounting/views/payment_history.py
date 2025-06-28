from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime, date

from apps.accounting.models import ServicePayment, ClientService
from apps.accounting.services.revenue_analytics_service import RevenueAnalyticsService
from apps.accounting.services.presentation_service import PresentationService
from apps.accounting.services.history_service import HistoryService
from apps.business_lines.models import BusinessLine


@login_required
def payment_history_view(request):
    analytics_service = RevenueAnalyticsService()
    
    filters = {
        'business_line': request.GET.get('business_line'),
        'category': request.GET.get('category'),
        'service_id': request.GET.get('service'),
    }
    period_type = request.GET.get('period', RevenueAnalyticsService.PeriodType.CURRENT_MONTH)
    
    payments_query = HistoryService.get_global_payments_history(
        {k: v for k, v in filters.items() if v}
    )
    
    payments_query = analytics_service._apply_period_filter(
        payments_query, period_type
    )
    
    paginator = Paginator(payments_query, 20)
    page = request.GET.get('page', 1)
    payments = paginator.get_page(page)
    
    context = {
        'payments': payments,
        'available_periods': [
            ('current_month', 'Mes actual'),
            ('last_month', 'Mes anterior'),
            ('current_year', 'Año actual'),
            ('last_year', 'Año anterior'),
            ('last_3_months', 'Últimos 3 meses'),
            ('last_6_months', 'Últimos 6 meses'),
            ('last_12_months', 'Últimos 12 meses'),
            ('all_time', 'Histórico total'),
        ],
        'selected_period': period_type,
        'filters': {
            'business_line': filters['business_line'],
            'category': filters['category'],
            'service': filters['service_id'],
        }
    }
    
    return render(request, 'accounting/payments/payment_history.html', context)
