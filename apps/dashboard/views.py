from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Value, Q
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from datetime import timedelta

from apps.accounting.models import ClientService, ServicePayment
from apps.expenses.models import Expense, ExpenseCategory
from apps.business_lines.models import BusinessLine

def get_net_revenue_aggregation():
    from django.db import models
    return Sum(F('amount') - Coalesce(F('refunded_amount'), Value(0, output_field=models.DecimalField())))


def get_temporal_data():
    today = timezone.now().date()
    start_date = today.replace(day=1) - timedelta(days=365)
    
    ingresos_por_mes = ServicePayment.objects.filter(
        payment_date__gte=start_date
    ).annotate(
        mes=TruncMonth('payment_date')
    ).values('mes').annotate(
        total=get_net_revenue_aggregation()
    ).order_by('mes')
    
    gastos_por_mes = Expense.objects.filter(
        date__gte=start_date,
        service_category='business'
    ).annotate(
        mes=TruncMonth('date')
    ).values('mes').annotate(
        total=Sum('amount')
    ).order_by('mes')
    
    ingresos_dict = {item['mes'].strftime('%Y-%m'): float(item['total'] or 0) for item in ingresos_por_mes}
    gastos_dict = {item['mes'].strftime('%Y-%m'): float(item['total'] or 0) for item in gastos_por_mes}
    
    months = []
    current_date = start_date
    while current_date <= today:
        month_key = current_date.strftime('%Y-%m')
        ingresos = ingresos_dict.get(month_key, 0)
        gastos = gastos_dict.get(month_key, 0)
        
        months.append({
            'month': current_date.strftime('%b %Y'),
            'ingresos': ingresos,
            'gastos': gastos,
            'beneficio': ingresos - gastos
        })
        
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return months[-12:]  # Últimos 12 meses


@login_required
def dashboard_home(request):
    
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)
    
    total_ingresos = ServicePayment.objects.aggregate(
        total=get_net_revenue_aggregation()
    )['total'] or 0
    
    ingresos_mes = ServicePayment.objects.filter(
        payment_date__gte=start_of_month
    ).aggregate(total=get_net_revenue_aggregation())['total'] or 0
    
    total_gastos = Expense.objects.filter(
        service_category='business'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    gastos_mes = Expense.objects.filter(
        date__gte=start_of_month,
        service_category='business'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    resultado_total = total_ingresos - total_gastos
    resultado_mes = ingresos_mes - gastos_mes
    
    margen_beneficio = (resultado_total / total_ingresos * 100) if total_ingresos > 0 else 0
    ingresos_diarios = ingresos_mes / 30 if ingresos_mes > 0 else 0
    
    lineas_negocio = []
    
    for bl in BusinessLine.objects.filter(parent__isnull=False):
        servicios = ClientService.objects.filter(business_line=bl)
        pagos = ServicePayment.objects.filter(client_service__in=servicios)
        
        ingresos_netos = pagos.aggregate(
            total=get_net_revenue_aggregation()
        )['total'] or 0
        
        lineas_negocio.append({
            'name': bl.name,
            'total_ingresos': ingresos_netos,
            'num_servicios': servicios.count(),
        })
    
    # Ordenar por ingresos totales
    lineas_negocio.sort(key=lambda x: x['total_ingresos'], reverse=True)
    
    gastos_por_categoria = ExpenseCategory.objects.annotate(
        total=Sum('expenses__amount', filter=Q(expenses__service_category='business')),
        count=Count('expenses', filter=Q(expenses__service_category='business'))
    ).filter(total__isnull=False).order_by('-total')
    
    # Datos temporales para gráficos
    temporal_data = get_temporal_data()
    
    context = {
        'page_title': 'Dashboard',
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'resultado_total': resultado_total,
        'ingresos_mes': ingresos_mes,
        'gastos_mes': gastos_mes,
        'resultado_mes': resultado_mes,
        'lineas_negocio': lineas_negocio,
        'gastos_por_categoria': gastos_por_categoria,
        'mes_actual': start_of_month.strftime('%B %Y'),
        'año_actual': start_of_year.year,
        'temporal_data': temporal_data,
        'margen_beneficio': margen_beneficio,
        'ingresos_diarios': ingresos_diarios,
    }

    return render(request, 'dashboard/home.html', context)
