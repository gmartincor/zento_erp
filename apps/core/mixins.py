from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import Q
from apps.core.constants import MONTHS_DICT, MONTHS_CHOICES, DEFAULT_START_YEAR, FINANCIAL_YEAR_RANGE_EXTENSION

class TemporalFilterMixin:
    def get_temporal_filters(self):
        current_year = timezone.now().year
        current_month = timezone.now().month
        
        try:
            year = int(self.request.GET.get('year', current_year))
            if year < DEFAULT_START_YEAR or year > current_year + FINANCIAL_YEAR_RANGE_EXTENSION:
                year = current_year
        except (ValueError, TypeError):
            year = current_year
        
        month_param = self.request.GET.get('month')
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
    
    def get_temporal_context(self):
        filters = self.get_temporal_filters()
        year = filters['year']
        month = filters['month']
        
        current_year = timezone.now().year
        
        context = {
            'current_year': year,
            'current_month': month,
            'current_month_name': MONTHS_DICT.get(month) if month else None,
            'available_years': list(range(DEFAULT_START_YEAR, current_year + FINANCIAL_YEAR_RANGE_EXTENSION + 1)),
            'available_months': MONTHS_CHOICES
        }
        
        return context
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_temporal_context())
        return context

class CategoryContextMixin:
    def get_category_context(self, category):
        return {
            'category': category,
            'category_slug': category.slug,
            'category_display': category.name,
            'category_type': category.category_type,
        }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        category = getattr(self, 'category', None)
        if not category and hasattr(self, 'object') and hasattr(self.object, 'category'):
            category = self.object.category
        if not category and hasattr(self, 'get_object'):
            try:
                obj = self.get_object()
                if hasattr(obj, 'category'):
                    category = obj.category
                elif obj.__class__.__name__ == 'ExpenseCategory':
                    category = obj
            except:
                pass
        
        if category:
            context.update(self.get_category_context(category))
        
        return context

class BusinessLinePermissionMixin:
    def get_allowed_business_lines(self):
        from apps.business_lines.models import BusinessLine
        return BusinessLine.objects.select_related('parent').all()
    
    def filter_business_lines_by_permission(self, queryset):
        return queryset
    
    def check_business_line_permission(self, business_line):
        return True
    
    def enforce_business_line_permission(self, business_line):
        pass

class CategoryNormalizationMixin:
    @staticmethod
    def normalize_category_for_url(category):
        return category.lower() if category else None
    
    @staticmethod
    def normalize_category_for_comparison(category):
        return category.upper() if category else None

class BusinessLineHierarchyMixin(CategoryNormalizationMixin):
    def resolve_business_line_from_path(self, line_path):
        from apps.business_lines.models import BusinessLine
        
        if not line_path:
            raise Http404("Ruta de línea de negocio no especificada.")
        
        path_parts = line_path.strip('/').split('/')
        
        if len(path_parts) == 1:
            try:
                return BusinessLine.objects.select_related('parent').get(
                    slug=path_parts[0], 
                    level=1
                )
            except BusinessLine.DoesNotExist:
                raise Http404(f"Línea de negocio '{path_parts[0]}' no encontrada.")
            except BusinessLine.MultipleObjectsReturned:
                raise Http404(f"Múltiples líneas de negocio encontradas con slug '{path_parts[0]}'. Contacte al administrador.")
        
        current_line = None
        for i, slug in enumerate(path_parts):
            try:
                if i == 0:
                    current_line = BusinessLine.objects.select_related('parent').get(
                        slug=slug, level=1
                    )
                else:
                    current_line = BusinessLine.objects.select_related('parent').get(
                        slug=slug, 
                        parent=current_line,
                        level=i + 1
                    )
            except BusinessLine.DoesNotExist:
                raise Http404(f"Línea de negocio '{slug}' no encontrada en el nivel {i + 1}.")
            except BusinessLine.MultipleObjectsReturned:
                raise Http404(f"Múltiples líneas de negocio encontradas con slug '{slug}' en el nivel {i + 1}. Contacte al administrador.")
        
        return current_line
    
    def get_hierarchy_path(self, business_line):
        if not business_line:
            return []
        
        path = []
        current = business_line
        
        while current:
            path.insert(0, current)
            current = current.parent
        
        return path
    
    def get_breadcrumb_path(self, business_line, category=None):
        from apps.accounting.services.navigation_service import HierarchicalNavigationService
        
        navigation_service = HierarchicalNavigationService()
        return navigation_service.build_breadcrumb_path(
            business_line=business_line,
            category=category,
            include_base=False
        )
    
    def get_business_line_context(self, line_path=None, category=None):
        context = {}
        
        if line_path:
            business_line = self.resolve_business_line_from_path(line_path)
            
            if hasattr(self, 'check_business_line_permission'):
                if not self.check_business_line_permission(business_line):
                    return {
                        'business_line': business_line,
                        'line_path': line_path,
                        'has_permission': False
                    }
            
            context.update({
                'business_line': business_line,
                'hierarchy_path': self.get_hierarchy_path(business_line),
                'breadcrumb_path': self.get_breadcrumb_path(business_line, category),
                'current_category': self.normalize_category_for_url(category),
                'line_path': line_path,
                'has_permission': True
            })
        
        return context

class ServiceCategoryMixin(CategoryNormalizationMixin):
    def get_services_by_category(self, business_line, category):
        from apps.accounting.models import ClientService
        
        queryset = ClientService.objects.get_services_by_category_including_descendants(
            business_line, category
        )
        
        if hasattr(self, 'filter_business_lines_by_permission'):
            queryset = self.filter_business_lines_by_permission(queryset)
        
        return queryset
    
    def get_category_stats(self, business_line, category):
        from django.db.models import Sum, Count
        from apps.accounting.models import ClientService
        
        stats_data = ClientService.objects.get_service_statistics_including_descendants(
            business_line, category
        )
        services = ClientService.objects.get_services_by_category_including_descendants(
            business_line, category
        )
        
        remanente_total = 0
        if category == 'BLACK':
            for service in services:
                remanente_total += service.get_remanente_total()

        return {
            'total_revenue': stats_data['total_revenue'],
            'service_count': stats_data['total_services'],
            'remanente_total': remanente_total,
            'avg_revenue_per_service': stats_data['avg_price'],
        }
    
    def get_category_display_name(self, category):
        return {
            'WHITE': 'Servicios White',
            'BLACK': 'Servicios Black'
        }.get(category, category)
    
    def validate_category(self, category):
        if category not in ['WHITE', 'BLACK']:
            raise Http404(f"Categoría '{category}' no válida.")
    
    def get_service_category_context(self, business_line, category):
        self.validate_category(category)
        
        services = self.get_services_by_category(business_line, category)
        stats = self.get_category_stats(business_line, category)
        
        return {
            'services': services,
            'current_category': self.normalize_category_for_url(category),
            'category_display': self.get_category_display_name(category),
            'category_stats': stats,
            'has_remanentes': category == 'BLACK' and business_line.has_remanente,
            'remanente_field': business_line.remanente_field if category == 'BLACK' else None,
        }
    
    def get_category_counts(self, business_line):
        from apps.accounting.models import ClientService
        
        descendant_ids = business_line.get_descendant_ids()
        base_queryset = ClientService.objects.filter(
            business_line__id__in=descendant_ids,
            is_active=True
        )
        
        if hasattr(self, 'filter_business_lines_by_permission'):
            base_queryset = self.filter_business_lines_by_permission(base_queryset)
        
        white_count = base_queryset.filter(category='WHITE').count()
        black_count = base_queryset.filter(category='BLACK').count()
        
        return {
            'white_count': white_count,
            'black_count': black_count,
        }
