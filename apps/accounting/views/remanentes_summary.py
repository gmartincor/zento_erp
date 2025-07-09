from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from datetime import datetime
from apps.business_lines.models import BusinessLine
from ..services.statistics_service import StatisticsService


@login_required
def remanentes_summary_view(request):
    year = request.GET.get('year')
    month = request.GET.get('month')
    search = request.GET.get('search', '').strip()
    business_line_id = request.GET.get('business_line')
    if business_line_id:
        try:
            business_line_id = int(business_line_id)
        except (ValueError, TypeError):
            business_line_id = None
    
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
    
    business_lines_choices = []
    for line in BusinessLine.objects.filter(is_active=True).order_by('name'):
        level_prefix = "  " * line.level
        business_lines_choices.append((line.id, f"{level_prefix}{line.name}"))
    
    context = {
        'page_title': 'Remanentes por Línea de Negocio',
        'page_subtitle': 'Análisis de remanentes por sublíneas de negocio',
        'selected_year': year or current_year,
        'selected_month': month,
        'search': search,
        'selected_business_line': business_line_id,
        'business_lines_choices': business_lines_choices,
        'years': range(current_year - 5, current_year + 1),
        'months': [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
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
        stats = StatisticsService().calculate_remanente_stats_filtered(
            business_line=line, year=year, month=month
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
            stats = StatisticsService().calculate_remanente_stats_filtered(
                business_line=selected_line, year=year, month=month
            )
            total_general = {
                'total_amount': stats['total_amount'],
                'has_remanentes': stats['has_remanentes']
            }
        except BusinessLine.DoesNotExist:
            stats = StatisticsService().calculate_remanente_stats_filtered(year=year, month=month)
            total_general = {
                'total_amount': stats['total_amount'],
                'has_remanentes': stats['has_remanentes']
            }
    else:
        total_amount = Decimal('0')
        has_remanentes = False
        
        for line_data in lines_data:
            total_amount += line_data['stats']['total_amount']
            if line_data['stats']['has_remanentes']:
                has_remanentes = True
        
        total_general = {
            'total_amount': total_amount,
            'has_remanentes': has_remanentes
        }
    
    context['total_general'] = total_general
    context['lines_data'] = lines_data
    
    return render(request, 'accounting/remanentes_summary.html', context)
