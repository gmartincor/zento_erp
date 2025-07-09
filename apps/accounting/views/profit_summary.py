from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum, F
from decimal import Decimal
from apps.expenses.models import Expense
from ..models import ServicePayment, ClientService
from ..services.payment_service import PaymentService


@login_required
def profit_summary_view(request, category='white'):
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    if year:
        try:
            year = int(year)
        except (ValueError, TypeError):
            year = None
    
    if month:
        try:
            month = int(month)
        except (ValueError, TypeError):
            month = None
    
    current_year = timezone.now().year
    current_month = timezone.now().month
    
    context = {
        'category': category,
        'category_display': 'White' if category == 'white' else 'Black',
        'page_title': f'Beneficios - Categoría {category.title()}',
        'page_subtitle': f'Análisis de beneficios por categoría - {category.title()}',
        'selected_year': year or current_year,
        'selected_month': month,
        'years': range(current_year - 5, current_year + 1),
        'months': [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ]
    }
    
    profit_data = calculate_profit_for_category(category, year, month)
    context.update(profit_data)
    
    return render(request, 'accounting/profit_summary.html', context)


def calculate_profit_for_category(category, year=None, month=None):
    payments = ServicePayment.objects.filter(
        client_service__category=category,
        status__in=[ServicePayment.StatusChoices.PAID, ServicePayment.StatusChoices.REFUNDED],
        amount__isnull=False
    )
    
    if year:
        payments = payments.filter(payment_date__year=year)
    if month:
        payments = payments.filter(payment_date__month=month)
    
    revenue_stats = PaymentService.calculate_revenue_stats(payments)
    total_revenue = revenue_stats['total_amount']
    
    expenses_filter = Q()
    if year:
        expenses_filter &= Q(accounting_year=year)
    if month:
        expenses_filter &= Q(accounting_month=month)
    
    total_expenses = Expense.objects.filter(expenses_filter).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    remanentes_filter = Q(category=category)
    if year:
        remanentes_filter &= Q(payments__payment_date__year=year)
    if month:
        remanentes_filter &= Q(payments__payment_date__month=month)
    
    if category == 'black':
        total_remanentes = ServicePayment.objects.filter(
            client_service__category=category,
            status__in=[ServicePayment.StatusChoices.PAID, ServicePayment.StatusChoices.REFUNDED],
            remanente__isnull=False
        )
        
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
