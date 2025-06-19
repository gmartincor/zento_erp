"""
Business Line Views - Business line management and navigation.

This module contains views related to business line operations,
following separation of concerns and DRY principles.
"""

from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.http import Http404
from django.db.models import Q
from django.contrib.auth.mixins import PermissionRequiredMixin

from apps.business_lines.models import BusinessLine
from apps.accounting.models import ClientService
from apps.accounting.services.template_service import TemplateDataService
from apps.accounting.services.presentation_service import PresentationService
from apps.core.mixins import (
    BusinessLinePermissionMixin,
    BusinessLineHierarchyMixin
)
from apps.core.constants import SERVICE_CATEGORIES


class BusinessLineDetailView(
    LoginRequiredMixin, 
    BusinessLinePermissionMixin, 
    BusinessLineHierarchyMixin,
    DetailView
):
    """
    Detail view for a specific business line.
    Shows children lines or category options if it's a leaf node.
    """
    model = BusinessLine
    template_name = 'accounting/business_line_detail.html'
    context_object_name = 'business_line'
    
    def get_object(self):
        """Get business line from hierarchical path."""
        line_path = self.kwargs.get('line_path', '')
        business_line = self.resolve_business_line_from_path(line_path)
        
        # Check permissions
        self.check_business_line_permission(business_line)
        
        return business_line
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use template service to prepare all context data
        template_service = TemplateDataService()
        detail_context = template_service.prepare_business_line_detail_context(self.object)
        
        # Add presentation data
        presentation_service = PresentationService()
        presentation_data = presentation_service.prepare_business_line_presentation(
            self.object, 
            self.request.user
        )
        
        context.update(detail_context)
        context['presentation'] = presentation_data
        return context


class BusinessLineListView(
    LoginRequiredMixin,
    BusinessLinePermissionMixin,
    ListView
):
    """
    List view for business lines accessible to the current user.
    """
    model = BusinessLine
    template_name = 'accounting/business_line_list.html'
    context_object_name = 'business_lines'
    paginate_by = 20
    
    def get_queryset(self):
        """Get business lines filtered by user permissions."""
        base_queryset = BusinessLine.objects.filter(is_active=True)
        filtered_queryset = self.filter_by_business_line_access(base_queryset)
        
        # Apply search if provided
        search_query = self.request.GET.get('search', '')
        if search_query:
            filtered_queryset = filtered_queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        return filtered_queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use template service to prepare all context data
        template_service = TemplateDataService()
        search_query = self.request.GET.get('search', '')
        
        list_context = template_service.prepare_business_line_list_context(
            business_lines=self.get_queryset(),
            search_query=search_query
        )
        
        context.update(list_context)
        return context


class BusinessLineHierarchyView(
    BusinessLineHierarchyMixin,
    PermissionRequiredMixin,
    TemplateView
):
    """
    Hierarchical navigation view for business lines.
    Displays business line structure and allows navigation through hierarchy.
    """
    permission_required = 'accounting.view_businessline'
    template_name = 'accounting/hierarchy_navigation.html'
    
    def get_context_data(self, **kwargs):
        """Enhanced context with hierarchical navigation data."""
        context = super().get_context_data(**kwargs)
        
        line_path = kwargs.get('line_path')
        
        if line_path:
            # Get hierarchy context for specific business line
            hierarchy_context = self.get_business_line_context(line_path)
            context.update(hierarchy_context)
            
            # Get the current business line and its children
            current_line = hierarchy_context.get('business_line')
            if current_line:
                from apps.accounting.services.business_line_service import BusinessLineService
                from apps.accounting.models import ClientService
                from django.db.models import Sum, Count, Q
                
                business_line_service = BusinessLineService()
                
                # Get children of current line
                children = BusinessLine.objects.filter(parent=current_line)
                accessible_children = business_line_service.get_accessible_lines(self.request.user).filter(
                    parent=current_line
                )
                
                # If no children, show service categories (BLACK/WHITE)
                if not accessible_children.exists():
                    # This is a leaf node - show categories
                    services = ClientService.objects.filter(business_line=current_line)
                    
                    # Calculate category statistics
                    black_services = services.filter(category='BLACK')
                    white_services = services.filter(category='WHITE')
                    
                    black_count = black_services.count()
                    white_count = white_services.count()
                    black_revenue = black_services.aggregate(total=Sum('price'))['total'] or 0
                    white_revenue = white_services.aggregate(total=Sum('price'))['total'] or 0
                    
                    # Create category items for display - ALWAYS show both BLACK and WHITE
                    category_items = []
                    
                    # Always add BLACK category
                    category_items.append({
                        'name': 'BLACK',
                        'category': 'BLACK',
                        'slug': 'black',
                        'type': 'category',
                        'count': black_count,
                        'total_revenue': black_revenue,
                        'total_services': black_count,
                        'url': f'/accounting/hierarchy/{line_path}/black/',
                        'description': f'{black_count} servicios BLACK'
                    })
                    
                    # Always add WHITE category
                    category_items.append({
                        'name': 'WHITE', 
                        'category': 'WHITE',
                        'slug': 'white',
                        'type': 'category',
                        'count': white_count,
                        'total_revenue': white_revenue,
                        'total_services': white_count,
                        'url': f'/accounting/hierarchy/{line_path}/white/',
                        'description': f'{white_count} servicios WHITE'
                    })
                    
                    context.update({
                        'current_line': current_line,
                        'items': category_items,
                        'show_categories': True,
                        'page_title': f'Categorías - {current_line.name}',
                        'page_subtitle': f'Categorías de servicios en {current_line.name}',
                        'subtitle': f'Categorías de servicios en {current_line.name}',
                        'show_hierarchy': True,
                        'view_type': 'categories',
                        'level_stats': {
                            'total_services': black_count + white_count,
                            'total_revenue': black_revenue + white_revenue,
                            'black_services': black_count,
                            'white_services': white_count,
                            'black_revenue': black_revenue,
                            'white_revenue': white_revenue,
                        }
                    })
                else:
                    # Has children - show business line hierarchy
                    current_line_services = ClientService.objects.filter(
                        business_line=current_line
                    ).count()
                    
                    current_line_revenue = ClientService.objects.filter(
                        business_line=current_line
                    ).aggregate(total=Sum('price'))['total'] or 0
                    
                    context.update({
                        'current_line': current_line,
                        'children': accessible_children,
                        'items': accessible_children,  # Template expects 'items'
                        'business_lines': accessible_children,
                        'page_title': f'Líneas de negocio - {current_line.name}',
                        'page_subtitle': f'Sublíneas de {current_line.name}',
                        'subtitle': f'Sublíneas de {current_line.name}',
                        'show_hierarchy': True,
                        'view_type': 'business_lines',
                        'level_stats': {
                            'current_line_services': current_line_services,
                            'current_line_revenue': current_line_revenue,
                            'children_count': accessible_children.count(),
                        }
                    })
        else:
            # Root level view - show all accessible root business lines
            from apps.accounting.services.business_line_service import BusinessLineService
            from apps.accounting.models import ClientService
            from django.db.models import Sum, Count
            
            business_line_service = BusinessLineService()
            
            accessible_lines = business_line_service.get_accessible_lines(self.request.user)
            root_lines = business_line_service.get_root_lines_for_user(self.request.user)
            
            # Calculate basic statistics
            total_services = ClientService.objects.filter(
                business_line__in=accessible_lines
            ).count()
            
            total_revenue = ClientService.objects.filter(
                business_line__in=accessible_lines
            ).aggregate(total=Sum('price'))['total'] or 0
            
            context.update({
                'business_lines': root_lines,
                'items': root_lines,  # Template expects 'items'
                'accessible_lines': accessible_lines,
                'page_title': 'Navegación Jerárquica',
                'page_subtitle': 'Explora la estructura de líneas de negocio',
                'subtitle': 'Explora la estructura de líneas de negocio',
                'show_hierarchy': True,
                'view_type': 'business_lines',
                'level_stats': {
                    'total_lines': accessible_lines.count(),
                    'total_revenue': total_revenue,
                    'total_services': total_services,
                    'avg_revenue_per_line': total_revenue / max(accessible_lines.count(), 1),
                }
            })
            
        return context


# Utility functions for business line operations
def get_business_line_path_hierarchy(business_line):
    """
    Get the hierarchical path for a business line.
    
    Args:
        business_line: BusinessLine instance
        
    Returns:
        List of ancestor business lines from root to current
    """
    hierarchy = []
    current = business_line
    
    while current:
        hierarchy.insert(0, current)
        current = current.parent
    
    return hierarchy


def build_business_line_breadcrumbs(business_line, view_name='accounting:business_line_detail'):
    """
    Build breadcrumb navigation for a business line.
    
    Args:
        business_line: BusinessLine instance
        view_name: URL name for business line detail view
        
    Returns:
        List of breadcrumb dictionaries with 'name' and 'url' keys
    """
    breadcrumbs = []
    hierarchy = get_business_line_path_hierarchy(business_line)
    
    for i, line in enumerate(hierarchy):
        # Build path for this level
        path_segments = [ancestor.slug for ancestor in hierarchy[:i+1]]
        line_path = '/'.join(path_segments)
        
        breadcrumbs.append({
            'name': line.name,
            'url': reverse(view_name, kwargs={'line_path': line_path}),
            'is_current': line == business_line
        })
    
    return breadcrumbs


def calculate_business_line_metrics(business_line):
    """
    Calculate key metrics for a business line.
    
    Args:
        business_line: BusinessLine instance
        
    Returns:
        Dictionary with calculated metrics
    """
    from apps.accounting.services.template_service import TemplateDataService
    
    template_service = TemplateDataService()
    return template_service.business_line_service.calculate_business_line_metrics(business_line)
