"""
Business Line Service - Enhanced business line operations.

This service provides a clean interface for business line operations,
following domain-driven design principles and separation of concerns.
"""

from django.db.models import Q, Sum, Count, Avg
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError

from apps.business_lines.models import BusinessLine
from apps.accounting.models import ClientService

User = get_user_model()


class BusinessLineService:
    """
    Service class for business line operations.
    
    Centralizes business logic for:
    - Hierarchical navigation
    - Permission management  
    - Business line statistics
    - Path resolution
    """
    
    def get_accessible_lines(self, user):
        """
        Get business lines accessible to the user based on role and permissions.
        
        Args:
            user: User instance
            
        Returns:
            QuerySet of accessible business lines
        """
        if user.role == 'ADMIN':
            return BusinessLine.objects.filter(is_active=True)
        elif user.role == 'GLOW_VIEWER':
            # Get lines assigned to user
            return user.business_lines.filter(is_active=True)
        else:
            return BusinessLine.objects.none()
    
    def get_root_lines_for_user(self, user):
        """
        Get root-level business lines accessible to the user.
        
        Args:
            user: User instance
            
        Returns:
            QuerySet of root business lines (level=1)
        """
        return self.get_accessible_lines(user).filter(level=1)
    
    def resolve_line_from_path(self, line_path):
        """
        Resolve a business line from hierarchical path.
        
        Args:
            line_path: Path like 'jaen/pepe/pepe-normal'
            
        Returns:
            BusinessLine instance
            
        Raises:
            BusinessLine.DoesNotExist: If path doesn't resolve
            ValidationError: If path format is invalid
        """
        if not line_path or not line_path.strip():
            raise ValidationError("Empty line path provided")
        
        path_parts = line_path.strip('/').split('/')
        
        # Single level (root)
        if len(path_parts) == 1:
            return BusinessLine.objects.get(
                slug=path_parts[0], 
                level=1, 
                is_active=True
            )
        
        # Multi-level path - navigate hierarchy
        current_line = None
        for i, slug in enumerate(path_parts):
            if i == 0:
                current_line = BusinessLine.objects.get(
                    slug=slug, 
                    level=1, 
                    is_active=True
                )
            else:
                current_line = BusinessLine.objects.get(
                    slug=slug,
                    parent=current_line,
                    level=i + 1,
                    is_active=True
                )
        
        return current_line
    
    def build_line_path(self, business_line):
        """
        Build hierarchical path string for a business line.
        
        Args:
            business_line: BusinessLine instance
            
        Returns:
            Path string like 'jaen/pepe/pepe-normal'
        """
        if not business_line:
            return ''
        
        path_parts = []
        current = business_line
        
        while current:
            path_parts.insert(0, current.slug)
            current = current.parent
        
        return '/'.join(path_parts)
    
    def check_user_permission(self, user, business_line):
        """
        Check if user has permission to access a business line.
        
        Args:
            user: User instance
            business_line: BusinessLine to check
            
        Returns:
            True if user has access, False otherwise
        """
        accessible_lines = self.get_accessible_lines(user)
        return accessible_lines.filter(id=business_line.id).exists()
    
    def enforce_permission(self, user, business_line):
        """
        Enforce permission check, raising exception if denied.
        
        Args:
            user: User instance
            business_line: BusinessLine to check
            
        Raises:
            PermissionDenied: If user doesn't have access
        """
        if not self.check_user_permission(user, business_line):
            raise PermissionDenied(
                f"User {user.username} does not have access to business line {business_line.name}"
            )
    
    def get_children_for_display(self, business_line, user_permissions=None):
        """
        Get child business lines for navigation display.
        
        Args:
            business_line: Parent business line
            user_permissions: Optional queryset of user's allowed business lines
            
        Returns:
            QuerySet of child business lines with annotations
        """
        children = business_line.children.filter(is_active=True)
        
        if user_permissions is not None:
            children = children.filter(id__in=user_permissions.values_list('id', flat=True))
        
        # Annotate with service counts for display
        children = children.annotate(
            white_service_count=Count(
                'client_services',
                filter=Q(client_services__category='WHITE', client_services__is_active=True)
            ),
            black_service_count=Count(
                'client_services',
                filter=Q(client_services__category='BLACK', client_services__is_active=True)
            )
        )
        
        return children.order_by('name')
    
    def get_hierarchical_view(self, accessible_lines):
        """
        Get business lines organized for hierarchical display.
        
        Args:
            accessible_lines: User's accessible business lines
            
        Returns:
            QuerySet ordered for hierarchy display
        """
        return accessible_lines.select_related('parent').order_by('level', 'name')
    
    def get_business_line_stats(self, business_line, include_children=False):
        """
        Get comprehensive statistics for a business line.
        
        Args:
            business_line: BusinessLine to analyze
            include_children: Whether to include statistics from child lines
            
        Returns:
            Dictionary with statistics
        """
        # Base queryset
        services_query = ClientService.objects.filter(
            business_line=business_line,
            is_active=True
        )
        
        # Include children if requested
        if include_children:
            child_lines = business_line.get_descendants(include_self=True)
            services_query = ClientService.objects.filter(
                business_line__in=child_lines,
                is_active=True
            )
        
        # Calculate statistics
        stats = services_query.aggregate(
            total_revenue=Sum('price'),
            total_services=Count('id'),
            avg_price=Avg('price'),
            white_count=Count('id', filter=Q(category='WHITE')),
            black_count=Count('id', filter=Q(category='BLACK')),
            white_revenue=Sum('price', filter=Q(category='WHITE')),
            black_revenue=Sum('price', filter=Q(category='BLACK')),
        )
        
        # Handle None values and add calculated fields
        stats['total_revenue'] = stats['total_revenue'] or 0
        stats['total_services'] = stats['total_services'] or 0
        stats['avg_price'] = stats['avg_price'] or 0
        stats['white_count'] = stats['white_count'] or 0
        stats['black_count'] = stats['black_count'] or 0
        stats['white_revenue'] = stats['white_revenue'] or 0
        stats['black_revenue'] = stats['black_revenue'] or 0
        
        # Add percentage calculations
        if stats['total_revenue'] > 0:
            stats['white_percentage'] = (stats['white_revenue'] / stats['total_revenue']) * 100
            stats['black_percentage'] = (stats['black_revenue'] / stats['total_revenue']) * 100
        else:
            stats['white_percentage'] = 0
            stats['black_percentage'] = 0
        
        return stats
