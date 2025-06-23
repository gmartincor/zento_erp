from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime, date

from apps.accounting.models import ServicePayment, ClientService
from apps.accounting.services.revenue_analytics_service import RevenueAnalyticsService
from apps.accounting.services.presentation_service import PresentationService
from apps.business_lines.models import BusinessLine


@login_required
def payment_history_view(request):
    analytics_service = RevenueAnalyticsService()
    presentation_service = PresentationService()
    
    business_line_path = request.GET.get('business_line')
    category = request.GET.get('category')
    service_id = request.GET.get('service')
    period_type = request.GET.get('period', RevenueAnalyticsService.PeriodType.CURRENT_MONTH)
    
    payments_query = ServicePayment.objects.filter(
        status=ServicePayment.StatusChoices.PAID
    ).select_related(
        'client_service__client',
        'client_service__business_line'
    ).order_by('-payment_date')
    
    if business_line_path:
        try:
            business_line = BusinessLine.objects.get(slug=business_line_path)
            payments_query = payments_query.filter(
                client_service__business_line=business_line
            )
        except BusinessLine.DoesNotExist:
            pass
    
    if category:
        payments_query = payments_query.filter(
            client_service__category=category.upper()
        )
    
    if service_id:
        payments_query = payments_query.filter(
            client_service_id=service_id
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
            'business_line': business_line_path,
            'category': category,
            'service': service_id,
        }
    }
    
    return render(request, 'accounting/payments/payment_history.html', context)
