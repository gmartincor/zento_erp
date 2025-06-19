"""
Business Line Views - CRUD operations with hierarchical navigation.

This module provides complete CRUD functionality for BusinessLine management
with seamless integration to the existing hierarchical navigation system,
following Django best practices and clean architecture principles.

Features:
- Full CRUD operations (Create, Read, Update, Delete)
- Hierarchical navigation integration
- Breadcrumb support
- Permission-based access control
- Dynamic parent selection
- Responsive UI integration
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, ListView
)
from django.core.exceptions import PermissionDenied

from .models import BusinessLine
from .forms import BusinessLineCreateForm, BusinessLineUpdateForm
from apps.core.mixins import BusinessLineHierarchyMixin, BusinessLinePermissionMixin
from apps.accounting.services.navigation_service import HierarchicalNavigationService


class AdminRequiredMixin(PermissionRequiredMixin):
    """
    Mixin to ensure only ADMIN users can access business line management.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """
        Check if user has ADMIN role before allowing access.
        """
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if getattr(request.user, 'role', None) != 'ADMIN':
            raise PermissionDenied(
                "Solo los administradores pueden gestionar líneas de negocio."
            )
        
        return super().dispatch(request, *args, **kwargs)


class BusinessLineBaseView(
    LoginRequiredMixin,
    AdminRequiredMixin,
    BusinessLineHierarchyMixin
):
    """
    Base view for all BusinessLine CRUD operations.
    
    Provides common functionality including:
    - Permission checking
    - Navigation context
    - Breadcrumb generation
    - Error handling
    """
    model = BusinessLine
    
    def get_context_data(self, **kwargs):
        """
        Add navigation and hierarchical context to all views.
        """
        context = super().get_context_data(**kwargs)
        
        # Initialize navigation service
        navigation_service = HierarchicalNavigationService()
        
        # Add basic navigation context
        context.update({
            'page_section': 'business_lines',
            'can_manage_business_lines': True,  # Admin only access
        })
        
        return context


class BusinessLineCreateView(BusinessLineBaseView, CreateView):
    """
    View for creating new BusinessLine instances.
    
    Supports both root-level creation and child creation under existing parents.
    Integrates with hierarchical navigation and provides dynamic parent selection.
    """
    form_class = BusinessLineCreateForm
    template_name = 'business_lines/business_line_form.html'
    
    def get_initial(self):
        """
        Set initial values based on context and URL parameters.
        """
        initial = super().get_initial()
        
        # Check for parent_id in URL parameters (for creating children)
        parent_id = self.request.GET.get('parent')
        if parent_id:
            try:
                parent = BusinessLine.objects.get(pk=parent_id, is_active=True)
                if parent.level < 3:  # Can only create children up to level 3
                    initial['parent'] = parent
                else:
                    messages.warning(
                        self.request,
                        f"No se pueden crear sublíneas bajo '{parent.name}' "
                        f"porque ya está en el nivel máximo."
                    )
            except BusinessLine.DoesNotExist:
                messages.error(self.request, "Línea padre no encontrada.")
        
        return initial
    
    def get_context_data(self, **kwargs):
        """
        Add creation-specific context.
        """
        context = super().get_context_data(**kwargs)
        
        # Determine if creating a child or root line
        parent_id = self.request.GET.get('parent')
        parent_line = None
        
        if parent_id:
            try:
                parent_line = BusinessLine.objects.get(pk=parent_id, is_active=True)
            except BusinessLine.DoesNotExist:
                pass
        
        # Generate breadcrumbs
        navigation_service = HierarchicalNavigationService()
        breadcrumb_path = navigation_service.build_breadcrumb_path(
            business_line=parent_line,
            include_base=True
        )
        
        # Add "Nueva línea" to breadcrumbs
        breadcrumb_path.append({
            'name': 'Nueva línea de negocio',
            'url': None,
            'is_current': True
        })
        
        context.update({
            'breadcrumb_path': breadcrumb_path,
            'parent_line': parent_line,
            'page_title': 'Crear Línea de Negocio',
            'page_subtitle': (
                f'Nueva sublínea en {parent_line.name}' if parent_line 
                else 'Nueva línea de negocio raíz'
            ),
            'form_action': 'create',
            'submit_text': 'Crear Línea de Negocio',
            'cancel_url': self.get_cancel_url(parent_line),
        })
        
        return context
    
    def get_cancel_url(self, parent_line=None):
        """
        Determine the appropriate cancel URL based on context.
        """
        if parent_line:
            # Return to parent's detail view in accounting
            from apps.accounting.services.business_line_service import BusinessLineService
            service = BusinessLineService()
            try:
                path = service.get_line_path(parent_line)
                return f'/accounting/business-lines/{path}/'
            except:
                pass
        
        # Default to business lines root
        return reverse('accounting:business-lines')
    
    def form_valid(self, form):
        """
        Handle successful form submission.
        """
        with transaction.atomic():
            response = super().form_valid(form)
            
            messages.success(
                self.request,
                f"Línea de negocio '{self.object.name}' creada exitosamente."
            )
            
            return response
    
    def form_invalid(self, form):
        """
        Handle form validation errors.
        """
        messages.error(
            self.request,
            "Por favor corrige los errores en el formulario."
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        """
        Redirect to the detail view of the created business line.
        """
        # Try to redirect to accounting detail view
        try:
            from apps.accounting.services.business_line_service import BusinessLineService
            service = BusinessLineService()
            path = service.get_line_path(self.object)
            return f'/accounting/business-lines/{path}/'
        except:
            # Fallback to business lines list
            return reverse('accounting:business-lines')


class BusinessLineUpdateView(BusinessLineBaseView, UpdateView):
    """
    View for updating existing BusinessLine instances.
    
    Handles complex hierarchy updates including recursive level adjustments
    for descendants when parent relationships change.
    """
    form_class = BusinessLineUpdateForm
    template_name = 'business_lines/business_line_form.html'
    context_object_name = 'business_line'
    
    def get_object(self, queryset=None):
        """
        Get the business line to update, with permission checking.
        """
        if queryset is None:
            queryset = self.get_queryset()
        
        pk = self.kwargs.get('pk')
        if not pk:
            raise Http404("ID de línea de negocio no especificado.")
        
        try:
            obj = queryset.get(pk=pk)
        except BusinessLine.DoesNotExist:
            raise Http404("Línea de negocio no encontrada.")
        
        return obj
    
    def get_context_data(self, **kwargs):
        """
        Add update-specific context including hierarchy information.
        """
        context = super().get_context_data(**kwargs)
        
        business_line = self.object
        
        # Generate breadcrumbs up to current line
        navigation_service = HierarchicalNavigationService()
        breadcrumb_path = navigation_service.build_breadcrumb_path(
            business_line=business_line,
            include_base=True
        )
        
        # Add "Editar" to breadcrumbs
        breadcrumb_path.append({
            'name': 'Editar',
            'url': None,
            'is_current': True
        })
        
        # Get statistics for impact assessment
        descendants_count = len(business_line.get_descendants_ids())
        services_count = business_line.client_services.filter(is_active=True).count()
        
        context.update({
            'breadcrumb_path': breadcrumb_path,
            'page_title': f'Editar - {business_line.name}',
            'page_subtitle': f'Línea de negocio nivel {business_line.level}',
            'form_action': 'update',
            'submit_text': 'Guardar Cambios',
            'cancel_url': self.get_cancel_url(),
            'descendants_count': descendants_count,
            'services_count': services_count,
            'has_dependencies': descendants_count > 0 or services_count > 0,
            'hierarchy_info': {
                'current_level': business_line.level,
                'parent': business_line.parent,
                'children_count': business_line.children.filter(is_active=True).count(),
                'full_path': business_line.get_full_hierarchy(),
            }
        })
        
        return context
    
    def get_cancel_url(self):
        """
        Return to the business line detail view.
        """
        try:
            from apps.accounting.services.business_line_service import BusinessLineService
            service = BusinessLineService()
            path = service.get_line_path(self.object)
            return f'/accounting/business-lines/{path}/'
        except:
            return reverse('accounting:business-lines')
    
    def form_valid(self, form):
        """
        Handle successful update with impact tracking.
        """
        old_parent = self.object.parent
        old_level = self.object.level
        
        with transaction.atomic():
            response = super().form_valid(form)
            
            # Check if hierarchy changed
            hierarchy_changed = (
                old_parent != self.object.parent or 
                old_level != self.object.level
            )
            
            if hierarchy_changed:
                descendants_updated = len(self.object.get_descendants_ids())
                if descendants_updated > 0:
                    messages.info(
                        self.request,
                        f"Se actualizaron automáticamente {descendants_updated} "
                        f"línea(s) descendiente(s) debido al cambio de jerarquía."
                    )
            
            messages.success(
                self.request,
                f"Línea de negocio '{self.object.name}' actualizada exitosamente."
            )
            
            return response
    
    def form_invalid(self, form):
        """
        Handle form validation errors with detailed feedback.
        """
        error_count = sum(len(errors) for errors in form.errors.values())
        messages.error(
            self.request,
            f"No se pudo actualizar la línea de negocio. "
            f"Se encontraron {error_count} error(es) en el formulario."
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        """
        Redirect to the updated business line detail view.
        """
        return self.get_cancel_url()


class BusinessLineDeleteView(BusinessLineBaseView, DeleteView):
    """
    View for soft-deleting BusinessLine instances.
    
    Implements cascade deletion rules and dependency checking
    to maintain data integrity.
    """
    template_name = 'business_lines/business_line_confirm_delete.html'
    context_object_name = 'business_line'
    success_url = reverse_lazy('accounting:business-lines')
    
    def get_object(self, queryset=None):
        """
        Get the business line to delete, with dependency checking.
        """
        obj = super().get_object(queryset)
        
        # Check for dependencies that prevent deletion
        self.dependency_check = self.check_deletion_dependencies(obj)
        
        return obj
    
    def check_deletion_dependencies(self, business_line):
        """
        Check for dependencies that would prevent safe deletion.
        
        Returns:
            dict: Dependency information
        """
        # Count active children
        active_children = business_line.children.filter(is_active=True).count()
        
        # Count active services
        active_services = business_line.client_services.filter(is_active=True).count()
        
        # Get descendant counts
        all_descendants = business_line.get_descendants_ids()
        total_descendants = len(all_descendants)
        
        return {
            'can_delete': active_children == 0 and active_services == 0,
            'active_children': active_children,
            'active_services': active_services,
            'total_descendants': total_descendants,
            'blocking_reason': self.get_blocking_reason(active_children, active_services)
        }
    
    def get_blocking_reason(self, active_children, active_services):
        """
        Get the reason why deletion is blocked.
        """
        reasons = []
        
        if active_children > 0:
            reasons.append(f"{active_children} sublínea(s) activa(s)")
        
        if active_services > 0:
            reasons.append(f"{active_services} servicio(s) activo(s)")
        
        if reasons:
            return "Tiene " + " y ".join(reasons)
        
        return None
    
    def get_context_data(self, **kwargs):
        """
        Add deletion-specific context with dependency information.
        """
        context = super().get_context_data(**kwargs)
        
        business_line = self.object
        
        # Generate breadcrumbs
        navigation_service = HierarchicalNavigationService()
        breadcrumb_path = navigation_service.build_breadcrumb_path(
            business_line=business_line,
            include_base=True
        )
        
        # Add "Eliminar" to breadcrumbs
        breadcrumb_path.append({
            'name': 'Eliminar',
            'url': None,
            'is_current': True
        })
        
        context.update({
            'breadcrumb_path': breadcrumb_path,
            'page_title': f'Eliminar - {business_line.name}',
            'page_subtitle': 'Confirmar eliminación de línea de negocio',
            'cancel_url': self.get_cancel_url(),
            'dependency_check': self.dependency_check,
            'hierarchy_info': {
                'level': business_line.level,
                'parent': business_line.parent,
                'full_path': business_line.get_full_hierarchy(),
            }
        })
        
        return context
    
    def get_cancel_url(self):
        """
        Return to the business line detail view.
        """
        try:
            from apps.accounting.services.business_line_service import BusinessLineService
            service = BusinessLineService()
            path = service.get_line_path(self.object)
            return f'/accounting/business-lines/{path}/'
        except:
            return reverse('accounting:business-lines')
    
    def post(self, request, *args, **kwargs):
        """
        Handle deletion with dependency validation.
        """
        self.object = self.get_object()
        
        # Re-check dependencies at deletion time
        dependency_check = self.check_deletion_dependencies(self.object)
        
        if not dependency_check['can_delete']:
            messages.error(
                request,
                f"No se puede eliminar '{self.object.name}': "
                f"{dependency_check['blocking_reason']}. "
                f"Elimina o desactiva las dependencias primero."
            )
            return redirect(self.get_cancel_url())
        
        # Perform soft deletion
        with transaction.atomic():
            name = self.object.name
            self.object.is_active = False
            self.object.save(update_fields=['is_active'])
            
            messages.success(
                request,
                f"Línea de negocio '{name}' eliminada exitosamente."
            )
        
        return redirect(self.success_url)


# Utility Views

class BusinessLineDetailView(BusinessLineBaseView, DetailView):
    """
    Detail view for BusinessLine with management actions.
    
    This view is primarily for administrative purposes and integrates
    with the accounting module's navigation system.
    """
    template_name = 'business_lines/business_line_detail.html'
    context_object_name = 'business_line'
    
    def get_context_data(self, **kwargs):
        """
        Add detailed information and management actions.
        """
        context = super().get_context_data(**kwargs)
        
        business_line = self.object
        
        # Generate breadcrumbs
        navigation_service = HierarchicalNavigationService()
        breadcrumb_path = navigation_service.build_breadcrumb_path(
            business_line=business_line,
            include_base=True
        )
        
        # Calculate statistics
        children = business_line.children.filter(is_active=True)
        services = business_line.client_services.filter(is_active=True)
        
        context.update({
            'breadcrumb_path': breadcrumb_path,
            'page_title': business_line.name,
            'page_subtitle': f'Línea de negocio - Nivel {business_line.level}',
            'children': children,
            'services_count': services.count(),
            'total_revenue': services.aggregate(Sum('price'))['price__sum'] or 0,
            'can_create_child': business_line.level < 3,
            'management_actions': True,
        })
        
        return context
