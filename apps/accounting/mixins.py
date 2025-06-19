"""
Business Line Mixins - Shared functionality for views.

This module contains mixins to eliminate code duplication and apply DRY principles
across business line views.
"""

from django.shortcuts import get_object_or_404
from django.http import Http404
from django.urls import reverse
from apps.business_lines.models import BusinessLine


class BusinessLinePathMixin:
    """
    Mixin for views that need to resolve business lines from hierarchical paths.
    
    Provides common functionality for:
    - Resolving line_path to BusinessLine objects
    - Building hierarchical URLs
    """
    
    def get_business_line_from_path(self, line_path=None):
        """
        Get business line by resolving hierarchical path.
        
        Args:
            line_path (str): Path like 'jaen/pepe/pepe-normal' or None to use from kwargs
            
        Returns:
            BusinessLine: The resolved business line object
            
        Raises:
            Http404: If the path doesn't resolve to a valid business line
        """
        if line_path is None:
            line_path = self.kwargs.get('line_path')
            
        if not line_path:
            raise Http404("No se proporcionó la ruta de la línea de negocio")
        
        # Split path and traverse hierarchy
        path_parts = line_path.split('/')
        current_line = None
        
        for slug in path_parts:
            if current_line is None:
                # Root level
                current_line = get_object_or_404(BusinessLine, slug=slug, parent=None)
            else:
                # Child level
                current_line = get_object_or_404(BusinessLine, slug=slug, parent=current_line)
        
        return current_line
    
    def get_object(self):
        """Standard get_object implementation using line_path."""
        return self.get_business_line_from_path()
    
    def get_business_line_url(self, business_line):
        """
        Get the detail URL for a business line.
        
        Args:
            business_line (BusinessLine): The business line object
            
        Returns:
            str: The URL for the business line detail page
        """
        return reverse('accounting:business-lines-path', kwargs={
            'line_path': business_line.get_url_path()
        })


class BusinessLineParentMixin:
    """
    Mixin for views that need to handle parent business lines (subline creation).
    """
    
    def get_parent_from_line_path(self):
        """Get parent business line from line_path parameter."""
        line_path = self.kwargs.get('line_path')
        if not line_path:
            return None
        
        # Use the BusinessLinePathMixin functionality
        if hasattr(self, 'get_business_line_from_path'):
            return self.get_business_line_from_path(line_path)
        
        # Fallback implementation if mixin not available
        path_parts = line_path.split('/')
        current_line = None
        
        for slug in path_parts:
            if current_line is None:
                current_line = get_object_or_404(BusinessLine, slug=slug, parent=None)
            else:
                current_line = get_object_or_404(BusinessLine, slug=slug, parent=current_line)
        
        return current_line
