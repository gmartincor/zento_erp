from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum, Count
from decimal import Decimal
from apps.business_lines.models import BusinessLine
from ..models import ServicePayment


@login_required
def revenue_summary_view(request, category='white'):
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
        'category': category,
        'category_display': 'White' if category == 'white' else 'Black',
        'page_title': f'Ingresos - Categoría {category.title()}',
        'page_subtitle': f'Análisis de ingresos por líneas de negocio - Categoría {category.title()}',
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
        stats = calculate_revenue_stats_filtered(
            business_line=line, category=category, year=year, month=month
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
            stats = calculate_revenue_stats_filtered(
                business_line=selected_line, category=category, year=year, month=month
            )
            total_summary = {
                'total_amount': stats['total_amount'],
                'total_payments': stats['total_payments'],
                'total_services': stats['total_services']
            }
        except BusinessLine.DoesNotExist:
            stats = calculate_revenue_stats_filtered(category=category, year=year, month=month)
            total_summary = {
                'total_amount': stats['total_amount'],
                'total_payments': stats['total_payments'],
                'total_services': stats['total_services']
            }
    else:
        total_amount = Decimal('0')
        total_payments = 0
        total_services = 0
        
        for line_data in lines_data:
            total_amount += line_data['stats']['total_amount']
            total_payments += line_data['stats']['total_payments']
            total_services += line_data['stats']['total_services']
        
        total_summary = {
            'total_amount': total_amount,
            'total_payments': total_payments,
            'total_services': total_services
        }
    
    context['total_summary'] = total_summary
    context['revenue_data'] = lines_data
    
    return render(request, 'accounting/revenue_summary.html', context)


def get_all_descendant_lines(business_line):
    descendants = [business_line]
    for child in business_line.children.filter(is_active=True):
        descendants.extend(get_all_descendant_lines(child))
    return descendants

def calculate_revenue_stats_filtered(business_line=None, category='white', year=None, month=None):
    if business_line:
        all_lines = get_all_descendant_lines(business_line)
        services = []
        for line in all_lines:
            services.extend(line.client_services.filter(category=category, is_active=True))
        
        if services:
            payments = ServicePayment.objects.filter(
                client_service__in=services,
                status=ServicePayment.StatusChoices.PAID
            )
        else:
            payments = ServicePayment.objects.none()
    else:
        payments = ServicePayment.objects.filter(
            client_service__category=category,
            status=ServicePayment.StatusChoices.PAID
        )
    
    if year:
        payments = payments.filter(payment_date__year=year)
    if month:
        payments = payments.filter(payment_date__month=month)
    
    summary = payments.aggregate(
        total_amount=Sum('amount'),
        total_payments=Count('id'),
        total_services=Count('client_service', distinct=True)
    )
    
    return {
        'total_amount': summary['total_amount'] or Decimal('0'),
        'total_payments': summary['total_payments'] or 0,
        'total_services': summary['total_services'] or 0,
    }
