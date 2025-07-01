from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta

from apps.accounting.models import ClientService, ServicePayment
from apps.expenses.models import Expense, ExpenseCategory
from apps.business_lines.models import BusinessLine

def get_net_revenue_aggregation():
    from django.db import models
    return Sum(F('amount') - Coalesce(F('refunded_amount'), Value(0, output_field=models.DecimalField())))


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
    
    total_gastos = Expense.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    gastos_mes = Expense.objects.filter(
        date__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    resultado_total = total_ingresos - total_gastos
    resultado_mes = ingresos_mes - gastos_mes
    
    # Calcular ingresos por línea de negocio usando el cálculo neto correcto
    lineas_negocio = []
    for bl in BusinessLine.objects.filter(parent__isnull=False):
        servicios = ClientService.objects.filter(business_line=bl)
        pagos = ServicePayment.objects.filter(client_service__in=servicios)
        
        ingresos_netos = pagos.aggregate(
            total=get_net_revenue_aggregation()
        )['total'] or 0
        
        gastos_total = Expense.objects.filter(business_line=bl).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        lineas_negocio.append({
            'name': bl.name,
            'business_line': bl,
            'total_ingresos': ingresos_netos,
            'total_gastos': gastos_total,
            'num_servicios': servicios.count(),
            'num_gastos': Expense.objects.filter(business_line=bl).count()
        })
    
    # Ordenar por ingresos totales
    lineas_negocio.sort(key=lambda x: x['total_ingresos'], reverse=True)
    
    gastos_por_categoria = ExpenseCategory.objects.annotate(
        total=Sum('expense__amount'),
        count=Count('expense')
    ).order_by('-total')
    
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
    }

    return render(request, 'dashboard/home.html', context)
