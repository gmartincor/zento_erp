from django.shortcuts import render
from django.contrib.auth.decorators import login_required
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
