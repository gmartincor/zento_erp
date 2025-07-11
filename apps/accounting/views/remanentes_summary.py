from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from datetime import datetime, timedelta
from apps.business_lines.models import BusinessLine
from ..services.statistics_service import StatisticsService


def _get_period_filters(period):
    today = timezone.now().date()
    
    if period == 'current_month':
        return {'year': today.year, 'month': today.month}
    elif period == 'last_month':
        last_month = today.replace(day=1) - timedelta(days=1)
        return {'year': last_month.year, 'month': last_month.month}
    elif period == 'current_year':
        return {'year': today.year, 'month': None}
    elif period == 'last_year':
        return {'year': today.year - 1, 'month': None}
    else:
        return {'year': None, 'month': None}


@login_required
def remanentes_summary_view(request):
    search = request.GET.get('search', '').strip()
    business_line_id = request.GET.get('business_line')
    period = request.GET.get('period', 'current_month')
    
    if business_line_id:
        try:
            business_line_id = int(business_line_id)
        except (ValueError, TypeError):
            business_line_id = None
    
    # Convertir período a year/month para compatibilidad con el servicio existente
    period_filters = _get_period_filters(period)
    year = period_filters['year']
    month = period_filters['month']
    
    business_lines_choices = []
    for line in BusinessLine.objects.filter(is_active=True).order_by('name'):
        level_prefix = "  " * line.level
        business_lines_choices.append((line.id, f"{level_prefix}{line.name}"))
    
    context = {
        'page_title': 'Remanentes por Línea de Negocio',
        'page_subtitle': 'Análisis de remanentes por sublíneas de negocio',
        'search': search,
        'selected_business_line': business_line_id,
        'business_lines_choices': business_lines_choices,
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
                'total_count': stats['total_count'],
                'has_remanentes': stats['has_remanentes']
            }
        except BusinessLine.DoesNotExist:
            stats = StatisticsService().calculate_remanente_stats_filtered(year=year, month=month)
            total_general = {
                'total_amount': stats['total_amount'],
                'total_count': stats['total_count'],
                'has_remanentes': stats['has_remanentes']
            }
    else:
        total_amount = Decimal('0')
        total_count = 0
        has_remanentes = False
        
        for line_data in lines_data:
            total_amount += line_data['stats']['total_amount']
            total_count += line_data['stats']['total_count']
            if line_data['stats']['has_remanentes']:
                has_remanentes = True
        
        total_general = {
            'total_amount': total_amount,
            'total_count': total_count,
            'has_remanentes': has_remanentes
        }
    
    context['total_general'] = total_general
    context['lines_data'] = lines_data
    
    return render(request, 'accounting/remanentes_summary.html', context)
