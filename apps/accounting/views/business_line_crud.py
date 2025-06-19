"""
Business Line CRUD Operations

This module handles Create, Read, Update, Delete operations for business lines
within the accounting context, following SRP and clean architecture principles.

Single Responsibility: Business line management operations only.
"""

from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.http import Http404

from apps.business_lines.models import BusinessLine


class AdminRequiredMixin:
    """Simple mixin to ensure only ADMIN users can manage business lines."""
    
    def dispatch(self, request, *args, **kwargs):
        if getattr(request.user, 'role', None) != 'ADMIN':
            raise PermissionDenied(
                "Solo los administradores pueden gestionar líneas de negocio."
            )
        return super().dispatch(request, *args, **kwargs)


class BusinessLineCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """
    Create new business lines.
    
    Single Responsibility: Handle business line creation with parent support.
    """
    model = BusinessLine
    template_name = 'business_lines/business_line_form.html'
    fields = ['name', 'parent']
    success_url = reverse_lazy('accounting:business-lines')
    
    def get_initial(self):
        """Set parent if provided in URL."""
        initial = super().get_initial()
        parent_id = self.kwargs.get('parent')
        if parent_id:
            try:
                parent = BusinessLine.objects.get(pk=parent_id)
                initial['parent'] = parent
            except BusinessLine.DoesNotExist:
                pass
        return initial
    
    def form_valid(self, form):
        """Handle successful creation with user feedback."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Línea de negocio "{self.object.name}" creada exitosamente.'
        )
        return response


class BusinessLineUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """
    Update existing business lines.
    
    Single Responsibility: Handle business line updates using line path.
    """
    model = BusinessLine
    template_name = 'business_lines/business_line_form.html'
    fields = ['name', 'parent']
    success_url = reverse_lazy('accounting:business-lines')
    
    def get_object(self):
        """Get business line by path instead of pk."""
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
    
    def form_valid(self, form):
        """Handle successful update with user feedback."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Línea de negocio "{self.object.name}" actualizada exitosamente.'
        )
        return response


class BusinessLineDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """
    Delete business lines with dependency checking using line path.
    
    Single Responsibility: Handle business line deletion safely.
    """
    model = BusinessLine
    template_name = 'business_lines/business_line_confirm_delete.html'
    success_url = reverse_lazy('accounting:business-lines')
    
    def get_object(self):
        """Get business line by path instead of pk."""
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
    
    def get_context_data(self, **kwargs):
        """Add dependency information to context."""
        context = super().get_context_data(**kwargs)
        
        # Simple dependency check
        business_line = self.object
        children_count = business_line.children.count()
        services_count = business_line.client_services.count()
        
        context.update({
            'children_count': children_count,
            'services_count': services_count,
            'can_delete': children_count == 0 and services_count == 0,
            'blocking_reason': self._get_blocking_reason(children_count, services_count)
        })
        
        return context
    
    def _get_blocking_reason(self, children, services):
        """Generate human-readable blocking reason."""
        reasons = []
        if children > 0:
            reasons.append(f"{children} sublínea(s)")
        if services > 0:
            reasons.append(f"{services} servicio(s)")
        
        if reasons:
            return f"No se puede eliminar porque tiene {' y '.join(reasons)} asociados."
        return None
    
    def delete(self, request, *args, **kwargs):
        """Override delete to add dependency checking."""
        business_line = self.get_object()
        
        # Check for dependencies
        if business_line.children.exists() or business_line.client_services.exists():
            messages.error(
                request,
                f'No se puede eliminar "{business_line.name}" porque tiene dependencias asociadas.'
            )
            return self.get(request, *args, **kwargs)
        
        # Safe to delete
        messages.success(
            request,
            f'Línea de negocio "{business_line.name}" eliminada exitosamente.'
        )
        return super().delete(request, *args, **kwargs)


class BusinessLineManagementDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """
    Administrative detail view for business lines using line path.
    
    Single Responsibility: Show management information and actions.
    """
    model = BusinessLine
    template_name = 'business_lines/business_line_detail.html'
    context_object_name = 'business_line'
    
    def get_object(self):
        """Get business line by path instead of pk."""
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
    
    def get_context_data(self, **kwargs):
        """Add management context."""
        context = super().get_context_data(**kwargs)
        business_line = self.object
        
        context.update({
            'children_count': business_line.children.count(),
            'services_count': business_line.client_services.count(),
            'is_management_view': True,
        })
        
        return context
