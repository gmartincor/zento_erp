from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import Q
from apps.core.services import parse_temporal_filters, get_temporal_context

class TemporalFilterMixin:
    def get_temporal_filters(self):
        return parse_temporal_filters(self.request)
    
    def get_temporal_context(self):
        filters = self.get_temporal_filters()
        return get_temporal_context(filters['year'], filters['month'])
    
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
        return category.lower() if category else None

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
        
        normalized_category = category.lower() if category else None
        
        queryset = ClientService.objects.get_services_by_category_including_descendants(
            business_line, normalized_category
        )
        
        if hasattr(self, 'filter_business_lines_by_permission'):
            queryset = self.filter_business_lines_by_permission(queryset)
        
        return queryset
    
    def get_category_stats(self, business_line, category):
        from django.db.models import Sum, Count
        from apps.accounting.models import ClientService
        
        normalized_category = category.lower() if category else None
        
        stats_data = ClientService.objects.get_service_statistics_including_descendants(
            business_line, normalized_category
        )
        services = ClientService.objects.get_services_by_category_including_descendants(
            business_line, normalized_category
        )
        
        remanente_total = 0
        if normalized_category == 'business':
            for service in services:
                remanente_total += service.get_remanente_total()

        return {
            'total_revenue': stats_data['total_revenue'],
            'service_count': stats_data['total_services'],
            'remanente_total': remanente_total,
            'avg_revenue_per_service': stats_data['avg_price'],
        }
    
    def get_category_display_name(self, category):
        normalized = category.lower() if category else None
        return {
            'personal': 'Servicios Personal',
            'business': 'Servicios Business'
        }.get(normalized, category)
    
    def validate_category(self, category):
        normalized_category = category.lower() if category else None
        if normalized_category not in ['personal', 'business']:
            raise Http404(f"Categoría '{category}' no válida.")
    
    def get_service_category_context(self, business_line, category):
        normalized_category = category.lower() if category else None
        self.validate_category(normalized_category)
        
        services = self.get_services_by_category(business_line, category)
        stats = self.get_category_stats(business_line, category)
        
        return {
            'services': services,
            'current_category': self.normalize_category_for_url(category),
            'category_display': self.get_category_display_name(category),
            'category_stats': stats,
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
        
        personal_count = base_queryset.filter(category='personal').count()
        business_count = base_queryset.filter(category='business').count()
        
        return {
            'personal_count': personal_count,
            'business_count': business_count,
        }

class TenantMixin:
    """Mixin para obtener información del tenant actual usando django-tenants"""
    
    def get_current_tenant(self):
        from django_tenants.utils import connection
        return connection.tenant
    
    def get_tenant_context(self):
        tenant = self.get_current_tenant()
        return {
            'tenant_name': tenant.name if tenant else None,
            'tenant_schema': tenant.schema_name if tenant else None,
        }
    
    def validate_tenant_access(self, user):
        tenant = self.get_current_tenant()
        if not tenant or not tenant.is_active:
            raise PermissionDenied("Acceso no autorizado al tenant")
        return True


class TenantContextMixin:
    """Mixin para contexto de gestión administrativa (no para tenants individuales)"""
    
    def get_admin_context(self):
        return {
            'admin_section': True,
            'app_section': 'administration',
            'breadcrumbs': self.get_admin_breadcrumbs(),
        }
    
    def get_admin_breadcrumbs(self):
        return [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Administración', 'url': '/admin/', 'active': True}
        ]


class TenantFormMixin:
    FORM_CSS_CLASSES = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
    
    def apply_form_styling(self, field, extra_attrs=None):
        attrs = {'class': self.FORM_CSS_CLASSES}
        if extra_attrs:
            attrs.update(extra_attrs)
        field.widget.attrs.update(attrs)
        return field


class ServiceCategoryFilterMixin:
    service_category = None
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.service_category:
            return queryset.filter(service_category=self.service_category)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.service_category:
            from apps.core.constants import EXPENSE_SERVICE_CATEGORY_DISPLAY
            context['service_category'] = self.service_category
            context['service_category_display'] = EXPENSE_SERVICE_CATEGORY_DISPLAY.get(self.service_category.upper(), self.service_category)
        return context
