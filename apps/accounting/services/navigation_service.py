"""
Hierarchical Navigation Service - Single Responsibility Principle

This service centralizes all navigation logic for hierarchical business lines,
following clean architecture principles and DRY methodology.

Responsibilities:
- Generate breadcrumb paths
- Build navigation context
- Handle hierarchy resolution
- Provide consistent navigation data across all views
"""

from typing import Dict, List, Optional, Any
from django.urls import reverse
from django.contrib.auth.models import AbstractUser

from apps.business_lines.models import BusinessLine


class HierarchicalNavigationService:
    """
    Service for managing hierarchical navigation in the accounting module.
    
    Centralizes breadcrumb generation and navigation context preparation
    to ensure consistency across all views and templates.
    """
    
    def __init__(self):
        """Initialize the navigation service."""
        self.base_breadcrumb_config = {
            'dashboard': {'name': 'Dashboard', 'url': 'dashboard:home'},
            'accounting': {'name': 'Ingresos', 'url': 'accounting:index'}
        }
    
    def get_hierarchy_path(self, business_line: BusinessLine) -> List[BusinessLine]:
        """
        Get the complete hierarchy path from root to current business line.
        
        Args:
            business_line: Target business line
            
        Returns:
            List of BusinessLine objects from root to current
        """
        if not business_line:
            return []
        
        path = []
        current = business_line
        
        while current:
            path.insert(0, current)
            current = current.parent
        
        return path
    
    def build_breadcrumb_path(
        self, 
        business_line: Optional[BusinessLine] = None, 
        category: Optional[str] = None,
        include_base: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Build complete breadcrumb path for navigation.
        
        Args:
            business_line: Current business line (optional)
            category: Service category (WHITE/BLACK, optional)
            include_base: Whether to include Dashboard/Accounting base items
            
        Returns:
            List of breadcrumb dictionaries with navigation data
        """
        breadcrumbs = []
        
        # Add base navigation items if requested
        if include_base:
            breadcrumbs.extend([
                {
                    'name': self.base_breadcrumb_config['dashboard']['name'],
                    'url': '/dashboard/',
                    'is_base': True
                },
                {
                    'name': self.base_breadcrumb_config['accounting']['name'], 
                    'url': '/accounting/',
                    'is_base': True
                }
            ])
        
        # Add business line hierarchy
        if business_line:
            hierarchy = self.get_hierarchy_path(business_line)
            url_parts = []
            
            for line in hierarchy:
                url_parts.append(line.slug)
                line_path = '/'.join(url_parts)
                
                # Generate the actual URL string instead of URL pattern + kwargs
                breadcrumbs.append({
                    'name': line.name,
                    'url': f'/accounting/business-lines/{line_path}/',
                    'business_line': line,
                    'level': line.level,
                    'is_active': True
                })
        
        # Add category if specified
        if category:
            category_display = self._format_category_name(category)
            breadcrumbs.append({
                'name': category_display,
                'url': None,  # Current page
                'category': category,
                'is_current': True
            })
        
        return breadcrumbs
    
    def build_navigation_context(
        self, 
        business_line: Optional[BusinessLine] = None,
        category: Optional[str] = None,
        user: Optional[AbstractUser] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive navigation context for templates.
        
        Args:
            business_line: Current business line
            category: Current category (optional)
            user: Current user for permission checking (optional)
            
        Returns:
            Dictionary with complete navigation context
        """
        context = {
            'breadcrumb_path': self.build_breadcrumb_path(business_line, category),
            'current_business_line': business_line,
            'current_category': category,
            'hierarchy_path': self.get_hierarchy_path(business_line) if business_line else [],
        }
        
        # Add business line specific context
        if business_line:
            context.update({
                'business_line': business_line,
                'business_line_level': business_line.level,
                'business_line_slug': business_line.slug,
                'has_children': business_line.children.filter(is_active=True).exists(),
                'is_leaf_node': not business_line.children.filter(is_active=True).exists(),
                'parent_line': business_line.parent,
                'siblings': self._get_siblings(business_line) if business_line.parent else []
            })
        
        # Add category specific context
        if category:
            context.update({
                'category_display': self._format_category_name(category),
                'category_slug': category.lower(),
                'is_category_view': True
            })
        
        return context
    
    def get_navigation_stats(
        self, 
        business_line: BusinessLine,
        include_children: bool = False
    ) -> Dict[str, Any]:
        """
        Get navigation statistics for display in breadcrumbs.
        
        Args:
            business_line: Business line to analyze
            include_children: Whether to include child statistics
            
        Returns:
            Dictionary with navigation statistics
        """
        from apps.accounting.models import ClientService
        from django.db.models import Count, Sum, Q
        
        # Base services query
        services = ClientService.objects.filter(
            business_line=business_line,
            is_active=True
        )
        
        # Include children if requested
        if include_children and business_line.children.exists():
            child_lines = business_line.children.filter(is_active=True)
            all_line_ids = [business_line.id] + list(child_lines.values_list('id', flat=True))
            services = ClientService.objects.filter(
                business_line__id__in=all_line_ids,
                is_active=True
            )
        
        # Calculate statistics
        stats = services.aggregate(
            total_services=Count('id'),
            total_revenue=Sum('price'),
            white_count=Count('id', filter=Q(category='WHITE')),
            black_count=Count('id', filter=Q(category='BLACK')),
            white_revenue=Sum('price', filter=Q(category='WHITE')),
            black_revenue=Sum('price', filter=Q(category='BLACK'))
        )
        
        # Clean up None values
        for key, value in stats.items():
            if value is None:
                stats[key] = 0
        
        return stats
    
    def _format_category_name(self, category: str) -> str:
        """Format category name for display."""
        if category.upper() == 'WHITE':
            return 'Servicios White'
        elif category.upper() == 'BLACK':
            return 'Servicios Black'
        return category.title()
    
    def _get_siblings(self, business_line: BusinessLine) -> List[BusinessLine]:
        """Get sibling business lines."""
        if not business_line.parent:
            return []
        
        return list(
            business_line.parent.children.filter(is_active=True)
            .exclude(id=business_line.id)
            .order_by('order', 'name')
        )
    
    def resolve_line_from_path(self, line_path: str) -> Optional[BusinessLine]:
        """
        Resolve business line from hierarchical path string.
        
        Args:
            line_path: Path like 'jaen/pepe/pepe-normal'
            
        Returns:
            BusinessLine instance or None if not found
        """
        if not line_path or not line_path.strip():
            return None
        
        try:
            path_parts = line_path.strip('/').split('/')
            
            # Single level (root)
            if len(path_parts) == 1:
                return BusinessLine.objects.select_related('parent').get(
                    slug=path_parts[0], 
                    level=1, 
                    is_active=True
                )
            
            # Multi-level path - navigate hierarchy
            current_line = None
            for i, slug in enumerate(path_parts):
                if i == 0:
                    current_line = BusinessLine.objects.select_related('parent').get(
                        slug=slug, 
                        level=1, 
                        is_active=True
                    )
                else:
                    current_line = BusinessLine.objects.select_related('parent').get(
                        slug=slug,
                        parent=current_line,
                        level=i + 1,
                        is_active=True
                    )
            
            return current_line
            
        except BusinessLine.DoesNotExist:
            return None
        except (ValueError, AttributeError):
            return None
