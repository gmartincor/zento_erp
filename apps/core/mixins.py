"""
Mixins for the CRM Nutrition Pro application.
Reusable mixins to reduce code duplication and improve maintainability.
"""

from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import Q
from apps.core.constants import MONTHS_DICT, MONTHS_CHOICES, DEFAULT_START_YEAR, FINANCIAL_YEAR_RANGE_EXTENSION


class TemporalFilterMixin:
    """
    Mixin that provides temporal filtering functionality for views.
    
    Adds common temporal filtering logic for year/month filters from GET parameters,
    and provides standardized context variables for templates.
    
    Context variables added:
    - current_year: Selected year (from GET param or current year)
    - current_month: Selected month (from GET param or None)
    - current_month_name: Name of selected month in Spanish
    - available_years: List of available years for selection
    - available_months: List of month choices for forms
    """
    
    def get_temporal_filters(self):
        """
        Extract and validate temporal filters from GET parameters.
        
        Returns:
            dict: Dictionary with temporal filter parameters
                - year: int, validated year
                - month: int or None, validated month
                - expense_filter: dict, ready-to-use filter for Expense queries
        """
        current_year = timezone.now().year
        current_month = timezone.now().month
        
        # Get and validate year parameter
        try:
            year = int(self.request.GET.get('year', current_year))
            # Validate year is within reasonable range
            if year < DEFAULT_START_YEAR or year > current_year + FINANCIAL_YEAR_RANGE_EXTENSION:
                year = current_year
        except (ValueError, TypeError):
            year = current_year
        
        # Get and validate month parameter
        month_param = self.request.GET.get('month')
        month = None
        if month_param:
            try:
                month = int(month_param)
                # Validate month is between 1-12
                if month < 1 or month > 12:
                    month = None
            except (ValueError, TypeError):
                month = None
        
        # Build expense filter dictionary
        expense_filter = {'accounting_year': year}
        if month:
            expense_filter['accounting_month'] = month
        
        return {
            'year': year,
            'month': month,
            'expense_filter': expense_filter
        }
    
    def get_temporal_context(self):
        """
        Get standardized temporal context for templates.
        
        Returns:
            dict: Context dictionary with temporal variables
        """
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
        """
        Override to automatically include temporal context in all views using this mixin.
        """
        context = super().get_context_data(**kwargs)
        context.update(self.get_temporal_context())
        return context


class CategoryContextMixin:
    """
    Mixin that provides standardized category context variables.
    
    Useful for views that work with ExpenseCategory objects to ensure
    consistent naming and availability of category-related context variables.
    """
    
    def get_category_context(self, category):
        """
        Get standardized category context variables.
        
        Args:
            category: ExpenseCategory instance
            
        Returns:
            dict: Context dictionary with category variables
        """
        return {
            'category': category,
            'category_slug': category.slug,
            'category_display': category.name,
            'category_type': category.category_type,  # For template compatibility
        }
    
    def get_context_data(self, **kwargs):
        """
        Override to automatically include category context if category is available.
        """
        context = super().get_context_data(**kwargs)
        
        # Try to get category from different possible sources
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
    """
    Mixin that provides business line permission filtering based on user roles.
    
    Automatically filters business lines based on user permissions:
    - ADMIN users: see all business lines
    - GLOW_VIEWER users: see only assigned business lines
    - Other roles: no access by default
    
    Usage:
        class MyView(BusinessLinePermissionMixin, ListView):
            def get_queryset(self):
                return self.filter_business_lines_by_permission(SomeModel.objects.all())
    """
    
    def get_allowed_business_lines(self):
        """
        Get business lines that the current user is allowed to access.
        
        Returns:
            QuerySet: BusinessLine objects accessible to the user
        """
        from apps.business_lines.models import BusinessLine
        
        user = self.request.user
        
        # Admin users can access all business lines
        if user.role == 'ADMIN':
            return BusinessLine.objects.select_related('parent').all()
        
        # GLOW_VIEWER users can only access their assigned business lines
        elif user.role == 'GLOW_VIEWER':
            return user.business_lines.select_related('parent').all()
        
        # Other roles have no access by default
        return BusinessLine.objects.none()
    
    def filter_business_lines_by_permission(self, queryset):
        """
        Filter a queryset to only include items related to allowed business lines.
        
        Args:
            queryset: Django QuerySet that has a business_line field
            
        Returns:
            QuerySet: Filtered queryset based on user permissions
        """
        allowed_lines = self.get_allowed_business_lines()
        
        if not allowed_lines.exists():
            return queryset.none()
        
        return queryset.filter(business_line__in=allowed_lines)
    
    def check_business_line_permission(self, business_line):
        """
        Check if the current user has permission to access a specific business line.
        
        Args:
            business_line: BusinessLine instance or ID
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        if isinstance(business_line, int):
            business_line_id = business_line
        else:
            business_line_id = business_line.id
        
        allowed_lines = self.get_allowed_business_lines()
        return allowed_lines.filter(id=business_line_id).exists()
    
    def enforce_business_line_permission(self, business_line):
        """
        Check business line permission and raise PermissionDenied if not allowed.
        
        Args:
            business_line: BusinessLine instance or ID
            
        Raises:
            PermissionDenied: If user doesn't have permission to access the business line
        """
        if not self.check_business_line_permission(business_line):
            raise PermissionDenied("No tienes permisos para acceder a esta línea de negocio.")


class BusinessLineHierarchyMixin:
    """
    Mixin that provides business line hierarchy navigation and path resolution.
    
    Handles hierarchical navigation through business lines and provides utilities
    for resolving paths like 'jaen/pepe/pepe-normal' to BusinessLine objects.
    
    Context variables added:
    - business_line: Current business line object
    - hierarchy_path: List of business line ancestors
    - breadcrumb_path: List of breadcrumb items for navigation
    """
    
    def resolve_business_line_from_path(self, line_path):
        """
        Resolve a hierarchical path to a BusinessLine object.
        
        Args:
            line_path (str): Path like 'jaen/pepe/pepe-normal' or single slug
            
        Returns:
            BusinessLine: The resolved business line object
            
        Raises:
            Http404: If the path doesn't resolve to a valid business line
        """
        from apps.business_lines.models import BusinessLine
        
        if not line_path:
            raise Http404("Ruta de línea de negocio no especificada.")
        
        # Split path into components
        path_parts = line_path.strip('/').split('/')
        
        if len(path_parts) == 1:
            # Single level path
            try:
                return BusinessLine.objects.select_related('parent').get(slug=path_parts[0])
            except BusinessLine.DoesNotExist:
                raise Http404(f"Línea de negocio '{path_parts[0]}' no encontrada.")
        
        # Multi-level path - navigate hierarchy
        current_line = None
        for i, slug in enumerate(path_parts):
            try:
                if i == 0:
                    # First level - no parent
                    current_line = BusinessLine.objects.select_related('parent').get(
                        slug=slug, level=1
                    )
                else:
                    # Subsequent levels - must have correct parent
                    current_line = BusinessLine.objects.select_related('parent').get(
                        slug=slug, 
                        parent=current_line,
                        level=i + 1
                    )
            except BusinessLine.DoesNotExist:
                raise Http404(f"Línea de negocio '{slug}' no encontrada en el nivel {i + 1}.")
        
        return current_line
    
    def get_hierarchy_path(self, business_line):
        """
        Get the complete hierarchy path for a business line.
        
        Args:
            business_line (BusinessLine): The business line object
            
        Returns:
            list: List of BusinessLine objects from root to current
        """
        if not business_line:
            return []
        
        path = []
        current = business_line
        
        while current:
            path.insert(0, current)
            current = current.parent
        
        return path
    
    def get_breadcrumb_path(self, business_line, category=None):
        """
        Generate breadcrumb navigation items for templates.
        
        Args:
            business_line (BusinessLine): Current business line
            category (str, optional): Current category (WHITE/BLACK)
            
        Returns:
            list: List of breadcrumb dictionaries with 'name' and 'url' keys
        """
        from apps.accounting.services.navigation_service import HierarchicalNavigationService
        
        navigation_service = HierarchicalNavigationService()
        return navigation_service.build_breadcrumb_path(
            business_line=business_line,
            category=category,
            include_base=False
        )
    
    def get_business_line_context(self, line_path=None, category=None):
        """
        Get comprehensive business line context for templates.
        
        Args:
            line_path (str, optional): Business line path to resolve
            category (str, optional): Service category (WHITE/BLACK)
            
        Returns:
            dict: Context dictionary with business line variables
        """
        context = {}
        
        if line_path:
            business_line = self.resolve_business_line_from_path(line_path)
            
            # Check permissions (but don't enforce to avoid redirect)
            if hasattr(self, 'check_business_line_permission'):
                if not self.check_business_line_permission(business_line):
                    # Return minimal context if no permissions
                    return {
                        'business_line': business_line,
                        'line_path': line_path,
                        'has_permission': False
                    }
            
            context.update({
                'business_line': business_line,
                'hierarchy_path': self.get_hierarchy_path(business_line),
                'breadcrumb_path': self.get_breadcrumb_path(business_line, category),
                'current_category': category,
                'line_path': line_path,
                'has_permission': True
            })
        
        return context


class ServiceCategoryMixin:
    """
    Mixin that provides service category filtering and context for WHITE/BLACK services.
    
    Handles filtering of ClientService objects by category and provides
    category-specific context and validation.
    
    Context variables added:
    - services: Filtered ClientService queryset
    - category_display: Human-readable category name
    - category_stats: Statistics for the current category
    """
    
    def get_services_by_category(self, business_line, category):
        """
        Get services filtered by business line and category.
        
        Args:
            business_line (BusinessLine): Business line to filter by
            category (str): Service category ('WHITE' or 'BLACK')
            
        Returns:
            QuerySet: Filtered ClientService objects with related data
        """
        from apps.accounting.models import ClientService
        
        queryset = ClientService.objects.select_related(
            'client', 'business_line'
        ).filter(
            business_line=business_line,
            category=category,
            is_active=True
        ).order_by('-created', 'client__full_name')
        
        # Apply permission filtering if available
        if hasattr(self, 'filter_business_lines_by_permission'):
            queryset = self.filter_business_lines_by_permission(queryset)
        
        return queryset
    
    def get_category_stats(self, business_line, category):
        """
        Calculate statistics for a category in a business line.
        
        Args:
            business_line (BusinessLine): Business line object
            category (str): Service category ('WHITE' or 'BLACK')
            
        Returns:
            dict: Statistics dictionary with totals and counts
        """
        from django.db.models import Sum, Count
        
        services = self.get_services_by_category(business_line, category)
        
        stats = services.aggregate(
            total_revenue=Sum('price'),
            service_count=Count('id')
        )
         # Calculate remanente total for BLACK category
        remanente_total = 0
        if category == 'BLACK':
            for service in services:
                remanente_total += service.get_remanente_total()
        
        # Calculate average revenue per service
        total_revenue = stats['total_revenue'] or 0
        service_count = stats['service_count'] or 0
        avg_revenue_per_service = total_revenue / service_count if service_count > 0 else 0

        return {
            'total_revenue': total_revenue,
            'service_count': service_count,
            'remanente_total': remanente_total,
            'avg_revenue_per_service': avg_revenue_per_service,
        }
    
    def get_category_display_name(self, category):
        """
        Get human-readable display name for category.
        
        Args:
            category (str): Category code ('WHITE' or 'BLACK')
            
        Returns:
            str: Display name
        """
        return {
            'WHITE': 'Servicios White',
            'BLACK': 'Servicios Black'
        }.get(category, category)
    
    def validate_category(self, category):
        """
        Validate that the category is valid.
        
        Args:
            category (str): Category to validate
            
        Raises:
            Http404: If category is not valid
        """
        if category not in ['WHITE', 'BLACK']:
            raise Http404(f"Categoría '{category}' no válida.")
    
    def get_service_category_context(self, business_line, category):
        """
        Get complete service category context for templates.
        
        Args:
            business_line (BusinessLine): Business line object
            category (str): Service category
            
        Returns:
            dict: Context dictionary with category-specific variables
        """
        self.validate_category(category)
        
        services = self.get_services_by_category(business_line, category)
        stats = self.get_category_stats(business_line, category)
        
        return {
            'services': services,
            'current_category': category,
            'category_display': self.get_category_display_name(category),
            'category_stats': stats,
            'has_remanentes': category == 'BLACK' and business_line.has_remanente,
            'remanente_field': business_line.remanente_field if category == 'BLACK' else None,
        }
    
    def get_category_counts(self, business_line):
        """
        Get service counts for both WHITE and BLACK categories.
        
        Args:
            business_line (BusinessLine): Business line object
            
        Returns:
            dict: Dictionary with white_count and black_count
        """
        from apps.accounting.models import ClientService
        
        base_queryset = ClientService.objects.filter(
            business_line=business_line,
            is_active=True
        )
        
        # Apply permission filtering if available
        if hasattr(self, 'filter_business_lines_by_permission'):
            base_queryset = self.filter_business_lines_by_permission(base_queryset)
        
        white_count = base_queryset.filter(category='WHITE').count()
        black_count = base_queryset.filter(category='BLACK').count()
        
        return {
            'white_count': white_count,
            'black_count': black_count,
        }
