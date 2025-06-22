from django.shortcuts import get_object_or_404
from django.http import Http404
from django.urls import reverse
from apps.business_lines.models import BusinessLine


class BusinessLinePathMixin:
    def get_business_line_from_path(self, line_path=None):
        if line_path is None:
            line_path = self.kwargs.get('line_path')
            
        if not line_path:
            raise Http404("No se proporcionó la ruta de la línea de negocio")
        
        path_parts = line_path.split('/')
        current_line = None
        
        for slug in path_parts:
            if current_line is None:
                current_line = get_object_or_404(BusinessLine, slug=slug, parent=None)
            else:
                current_line = get_object_or_404(BusinessLine, slug=slug, parent=current_line)
        
        return current_line
    
    def get_object(self):
        return self.get_business_line_from_path()
    
    def get_business_line_url(self, business_line):
        return reverse('accounting:business-lines-path', kwargs={
            'line_path': business_line.get_url_path()
        })


class BusinessLineParentMixin:
    def get_parent_from_line_path(self):
        line_path = self.kwargs.get('line_path')
        if not line_path:
            return None
        
        if hasattr(self, 'get_business_line_from_path'):
            return self.get_business_line_from_path(line_path)
        
        path_parts = line_path.split('/')
        current_line = None
        
        for slug in path_parts:
            if current_line is None:
                current_line = get_object_or_404(BusinessLine, slug=slug, parent=None)
            else:
                current_line = get_object_or_404(BusinessLine, slug=slug, parent=current_line)
        
        return current_line
