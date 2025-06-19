"""
Business Line Manager - Complex queries for business lines.

This manager handles hierarchical navigation, permission filtering,
and complex business line operations with optimized queries.
"""

from typing import List, Dict, Optional, Any
from django.db import models
from django.db.models import QuerySet, Q, Sum, Count, F
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()


class BusinessLineQuerySet(models.QuerySet):
    """Custom QuerySet for BusinessLine with common filters."""
    
    def active(self):
        """Filter only active business lines."""
        return self.filter(is_active=True)
    
    def roots(self):
        """Filter only root-level business lines."""
        return self.filter(level=1)
    
    def children_of(self, parent):
        """Filter children of a specific parent."""
        return self.filter(parent=parent)
    
    def with_service_counts(self):
        """Annotate with service counts for performance."""
        return self.annotate(
            total_services=Count(
                'client_services',
                filter=Q(client_services__is_active=True)
            ),
            white_services=Count(
                'client_services',
                filter=Q(
                    client_services__category='WHITE',
                    client_services__is_active=True
                )
            ),
            black_services=Count(
                'client_services',
                filter=Q(
                    client_services__category='BLACK',
                    client_services__is_active=True
                )
            ),
            total_revenue=Sum(
                'client_services__price',
                filter=Q(client_services__is_active=True)
            )
        )


class BusinessLineManager(models.Manager):
    """
    Custom manager for BusinessLine with hierarchical operations.
    
    Handles complex queries related to business line hierarchy,
    user permissions, and navigation operations.
    """
    
    def get_queryset(self):
        """Return custom QuerySet."""
        return BusinessLineQuerySet(self.model, using=self._db)
    
    def active(self):
        """Get only active business lines."""
        return self.get_queryset().active()
    
    def roots(self):
        """Get only root-level business lines."""
        return self.get_queryset().roots()
    
    def get_accessible_lines_for_user(self, user: User) -> QuerySet:
        """
        Get business lines accessible to a user based on their role.
        
        Args:
            user: User instance
            
        Returns:
            QuerySet of accessible business lines
        """
        if user.role == 'ADMIN':
            return self.active()
        elif user.role == 'GLOW_VIEWER':
            # Get assigned business lines and their descendants
            assigned_lines = user.business_lines.filter(is_active=True)
            accessible_ids = set()
            
            for line in assigned_lines:
                accessible_ids.add(line.id)
                # Add all descendants
                self._collect_descendant_ids(line, accessible_ids)
            
            return self.active().filter(id__in=accessible_ids)
        else:
            return self.none()
    
    def get_root_lines_for_user(self, user: User) -> QuerySet:
        """
        Get root-level business lines accessible to a user.
        
        Args:
            user: User instance
            
        Returns:
            QuerySet of root business lines with statistics
        """
        if user.role == 'ADMIN':
            root_lines = self.roots().active()
        elif user.role == 'GLOW_VIEWER':
            # Get root lines that contain user's assigned lines
            assigned_lines = user.business_lines.all()
            root_ids = set()
            
            for line in assigned_lines:
                # Find root ancestor
                current = line
                while current.parent:
                    current = current.parent
                root_ids.add(current.id)
            
            root_lines = self.roots().active().filter(id__in=root_ids)
        else:
            root_lines = self.none()
        
        return root_lines.with_service_counts().order_by('name')
    
    def get_line_by_path(self, line_path: str):
        """
        Resolve a business line from hierarchical path.
        
        Args:
            line_path: Path like 'jaen/pepe/pepe-normal'
            
        Returns:
            BusinessLine instance
            
        Raises:
            ObjectDoesNotExist: If path doesn't resolve
        """
        if not line_path:
            raise ObjectDoesNotExist("Empty path provided")
        
        path_parts = line_path.strip('/').split('/')
        
        if len(path_parts) == 1:
            return self.get(slug=path_parts[0], level=1, is_active=True)
        
        # Navigate through hierarchy
        current_line = None
        for i, slug in enumerate(path_parts):
            if i == 0:
                current_line = self.get(slug=slug, level=1, is_active=True)
            else:
                current_line = self.get(
                    slug=slug,
                    parent=current_line,
                    is_active=True
                )
        
        return current_line
    
    def get_children_for_display(
        self,
        business_line,
        accessible_lines: QuerySet
    ) -> QuerySet:
        """
        Get child business lines that should be displayed.
        
        Args:
            business_line: Parent business line
            accessible_lines: Lines accessible to current user
            
        Returns:
            QuerySet of child business lines
        """
        children = self.get_queryset().filter(
            parent=business_line,
            id__in=accessible_lines
        ).active().with_service_counts().order_by('name')
        
        return children
    
    def get_hierarchy_path(self, business_line) -> List[Dict[str, Any]]:
        """
        Get the full hierarchy path for a business line.
        
        Args:
            business_line: BusinessLine instance
            
        Returns:
            List of hierarchy elements from root to current
        """
        path = []
        current = business_line
        
        # Build path from leaf to root
        while current:
            path.insert(0, {
                'id': current.id,
                'name': current.name,
                'slug': current.slug,
                'level': current.level
            })
            current = current.parent
        
        return path
    
    def get_descendants(self, business_line) -> QuerySet:
        """
        Get all descendants of a business line.
        
        Args:
            business_line: Parent business line
            
        Returns:
            QuerySet of descendant business lines
        """
        descendant_ids = set()
        self._collect_descendant_ids(business_line, descendant_ids)
        
        return self.active().filter(id__in=descendant_ids)
    
    def get_business_lines_with_services(
        self,
        accessible_lines: QuerySet
    ) -> QuerySet:
        """
        Get business lines that have active services.
        
        Args:
            accessible_lines: Lines accessible to current user
            
        Returns:
            QuerySet of business lines with services
        """
        return accessible_lines.filter(
            client_services__is_active=True
        ).distinct().with_service_counts()
    
    def search_business_lines(
        self,
        query: str,
        accessible_lines: QuerySet
    ) -> QuerySet:
        """
        Search business lines by name or description.
        
        Args:
            query: Search query
            accessible_lines: Lines accessible to current user
            
        Returns:
            QuerySet of matching business lines
        """
        return accessible_lines.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(slug__icontains=query)
        ).with_service_counts()
    
    def get_business_line_statistics(
        self,
        business_line,
        include_descendants: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a business line.
        
        Args:
            business_line: BusinessLine to analyze
            include_descendants: Whether to include descendant statistics
            
        Returns:
            Dictionary with statistics
        """
        from apps.accounting.models import ClientService
        
        # Base filter
        if include_descendants:
            descendant_ids = {business_line.id}
            self._collect_descendant_ids(business_line, descendant_ids)
            services_filter = Q(business_line_id__in=descendant_ids, is_active=True)
        else:
            services_filter = Q(business_line=business_line, is_active=True)
        
        # Get statistics
        stats = ClientService.objects.filter(services_filter).aggregate(
            total_services=Count('id'),
            total_revenue=Sum('price'),
            unique_clients=Count('client', distinct=True),
            white_services=Count('id', filter=Q(category='WHITE')),
            black_services=Count('id', filter=Q(category='BLACK')),
            white_revenue=Sum('price', filter=Q(category='WHITE')),
            black_revenue=Sum('price', filter=Q(category='BLACK'))
        )
        
        return {
            'business_line': business_line,
            'total_services': stats['total_services'] or 0,
            'total_revenue': stats['total_revenue'] or 0,
            'unique_clients': stats['unique_clients'] or 0,
            'white_services': stats['white_services'] or 0,
            'black_services': stats['black_services'] or 0,
            'white_revenue': stats['white_revenue'] or 0,
            'black_revenue': stats['black_revenue'] or 0,
            'include_descendants': include_descendants
        }
    
    def _collect_descendant_ids(
        self,
        business_line,
        id_set: set
    ) -> None:
        """
        Recursively collect descendant IDs.
        
        Args:
            business_line: Parent business line
            id_set: Set to collect IDs into
        """
        children = self.get_queryset().filter(
            parent=business_line,
            is_active=True
        )
        
        for child in children:
            id_set.add(child.id)
            self._collect_descendant_ids(child, id_set)
