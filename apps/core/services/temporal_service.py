from django.utils import timezone
from apps.core.constants import DEFAULT_START_YEAR, FINANCIAL_YEAR_BUFFER, MONTHS_DICT, MONTHS_CHOICES


def get_available_years():
    current_year = timezone.now().year
    return list(range(DEFAULT_START_YEAR, current_year + FINANCIAL_YEAR_BUFFER + 1))


def get_temporal_context(year=None, month=None):
    current_year = timezone.now().year
    
    if not year:
        year = current_year
        
    return {
        'current_year': year,
        'current_month': month,
        'current_month_name': MONTHS_DICT.get(month) if month else None,
        'available_years': get_available_years(),
        'available_months': MONTHS_CHOICES
    }


def parse_temporal_filters(request):
    current_year = timezone.now().year
    
    try:
        year = int(request.GET.get('year', current_year))
        if year < DEFAULT_START_YEAR or year > current_year + FINANCIAL_YEAR_BUFFER:
            year = current_year
    except (ValueError, TypeError):
        year = current_year
    
    month_param = request.GET.get('month')
    month = None
    if month_param:
        try:
            month = int(month_param)
            if month < 1 or month > 12:
                month = None
        except (ValueError, TypeError):
            month = None
    
    expense_filter = {'accounting_year': year}
    if month:
        expense_filter['accounting_month'] = month
    
    return {
        'year': year,
        'month': month,
        'expense_filter': expense_filter
    }
