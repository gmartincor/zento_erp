from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta

from apps.accounting.models import ClientService
from apps.expenses.models import Expense, ExpenseCategory
from apps.business_lines.models import BusinessLine


@login_required
def dashboard_home(request):
    """Vista principal del dashboard con métricas básicas."""
    
    # Obtener fechas para filtros
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)
    
    # Métricas de ingresos
    total_ingresos = ClientService.objects.aggregate(
        total=Sum('price')
    )['total'] or 0
    
    ingresos_mes = ClientService.objects.filter(
        start_date__gte=start_of_month
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Métricas de gastos
    total_gastos = Expense.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    gastos_mes = Expense.objects.filter(
        date__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Resultado neto
    resultado_total = total_ingresos - total_gastos
    resultado_mes = ingresos_mes - gastos_mes
    
    # Distribución por líneas de negocio
    lineas_negocio = BusinessLine.objects.filter(
        parent__isnull=False  # Solo líneas de negocio de nivel 2/3
    ).annotate(
        total_ingresos=Sum('clientservice__price'),
        total_gastos=Sum('expense__amount'),
        num_servicios=Count('clientservice'),
        num_gastos=Count('expense')
    ).order_by('-total_ingresos')
    
    # Gastos por categoría
    gastos_por_categoria = ExpenseCategory.objects.annotate(
        total=Sum('expense__amount'),
        count=Count('expense')
    ).order_by('-total')
    
    context = {
        'page_title': 'Dashboard',
        # Métricas principales
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'resultado_total': resultado_total,
        'ingresos_mes': ingresos_mes,
        'gastos_mes': gastos_mes,
        'resultado_mes': resultado_mes,
        # Datos para gráficos
        'lineas_negocio': lineas_negocio,
        'gastos_por_categoria': gastos_por_categoria,
        # Fechas
        'mes_actual': start_of_month.strftime('%B %Y'),
        'año_actual': start_of_year.year,
    }

    return render(request, 'dashboard/home.html', context)
