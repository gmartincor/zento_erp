from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from .services import DashboardDataService


@login_required
def dashboard_home(request):
    service = DashboardDataService()
    
    financial_summary = service.get_financial_summary()
    temporal_data = service.get_temporal_data()
    business_lines = service.get_business_lines_data()
    expense_categories = service.get_expense_categories_data()
    
    context = {
        **financial_summary,
        'temporal_data': temporal_data,
        'lineas_negocio': business_lines,
        'gastos_por_categoria': expense_categories,
    }

    return render(request, 'dashboard/home.html', context)

@login_required
def get_filtered_business_lines(request):
    start_date = parse_date(request.GET.get('start_date')) if request.GET.get('start_date') else None
    end_date = parse_date(request.GET.get('end_date')) if request.GET.get('end_date') else None
    
    business_lines = DashboardDataService.get_business_lines_data(start_date, end_date)
    
    return JsonResponse({
        'business_lines_data': [
            {
                'nombre': bl['name'],
                'ingresos': float(bl['total_ingresos']),
                'porcentaje': float(bl['porcentaje'])
            }
            for bl in business_lines
        ]
    })

@login_required
def get_filtered_expenses(request):
    start_date = parse_date(request.GET.get('start_date')) if request.GET.get('start_date') else None
    end_date = parse_date(request.GET.get('end_date')) if request.GET.get('end_date') else None
    
    expense_categories = DashboardDataService.get_expense_categories_data(start_date, end_date)
    
    return JsonResponse({
        'expenses_data': [
            {
                'categoria': cat.name,
                'total': float(cat.total) if cat.total else 0,
                'porcentaje': float(cat.porcentaje)
            }
            for cat in expense_categories
        ]
    })
