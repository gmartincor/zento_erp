from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404
from django.http import Http404

from apps.business_lines.models import BusinessLine
from ..mixins import BusinessLinePathMixin, BusinessLineParentMixin


class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if getattr(request.user, 'role', None) != 'ADMIN':
            raise PermissionDenied(
                "Solo los administradores pueden gestionar líneas de negocio."
            )
        return super().dispatch(request, *args, **kwargs)


class BusinessLineCreateView(
    LoginRequiredMixin, 
    AdminRequiredMixin, 
    BusinessLineParentMixin,
    BusinessLinePathMixin,
    CreateView
):
    model = BusinessLine
    template_name = 'business_lines/business_line_form.html'
    fields = ['name', 'parent']
    
    def get_initial(self):
        initial = super().get_initial()
        parent = self.get_parent_from_line_path()
        if parent:
            initial['parent'] = parent
        else:
            parent_id = self.kwargs.get('parent')
            if parent_id:
                try:
                    parent = BusinessLine.objects.get(pk=parent_id)
                    initial['parent'] = parent
                except BusinessLine.DoesNotExist:
                    pass
        return initial
    
    def get_success_url(self):
        return self.get_business_line_url(self.object)
    
    def get_initial(self):
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
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Línea de negocio "{self.object.name}" creada exitosamente.'
        )
        return response


class BusinessLineUpdateView(
    LoginRequiredMixin, 
    AdminRequiredMixin, 
    BusinessLinePathMixin,
    UpdateView
):
    model = BusinessLine
    template_name = 'business_lines/business_line_form.html'
    fields = ['name', 'parent']
    
    def get_success_url(self):
        return self.get_business_line_url(self.object)
    
    def get_object(self):
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
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Línea de negocio "{self.object.name}" actualizada exitosamente.'
        )
        return response


class BusinessLineDeleteView(
    LoginRequiredMixin, 
    AdminRequiredMixin, 
    BusinessLinePathMixin,
    DeleteView
):
    model = BusinessLine
    template_name = 'business_lines/business_line_confirm_delete.html'
    success_url = reverse_lazy('accounting:business-lines')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business_line = self.object
        children_count = business_line.children.count()
        services_count = business_line.client_services.count()
        total_descendants = self._count_total_descendants(business_line)
        total_services = self._count_total_services(business_line)
        context.update({
            'children_count': children_count,
            'services_count': services_count,
            'total_descendants': total_descendants,
            'total_services': total_services,
            'can_delete': True,
            'deletion_safe': True,
            'blocking_reason': None,
            'cascade_warning': self._get_cascade_warning(children_count, total_descendants, total_services)
        })
        return context
    
    def _count_total_descendants(self, business_line):
        count = business_line.children.count()
        for child in business_line.children.all():
            count += self._count_total_descendants(child)
        return count
    
    def _count_total_services(self, business_line):
        count = business_line.client_services.count()
        for child in business_line.children.all():
            count += self._count_total_services(child)
        return count
    
    def _get_cascade_warning(self, children, total_descendants, total_services):
        if children == 0 and total_services == 0:
            return None
        warnings = []
        if total_descendants > 0:
            warnings.append(f"{total_descendants} sublínea(s)")
        if total_services > 0:
            warnings.append(f"{total_services} servicio(s)")
        return f"Se eliminarán también: {' y '.join(warnings)}"
    
    def delete(self, request, *args, **kwargs):
        business_line = self.get_object()
        business_line_name = business_line.name
        children_count = business_line.children.count()
        services_count = business_line.client_services.count()
        if children_count > 0:
            messages.warning(
                request,
                f'Al eliminar "{business_line_name}" se eliminarán también sus {children_count} sublínea(s) y todos sus servicios asociados. Esta acción no se puede deshacer.'
            )
            result = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                f'Línea de negocio "{business_line_name}" y sus {children_count} sublínea(s) eliminadas exitosamente.'
            )
        else:
            result = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                f'Línea de negocio "{business_line_name}" eliminada exitosamente.'
            )
        return result


class BusinessLineManagementDetailView(
    LoginRequiredMixin, 
    AdminRequiredMixin, 
    BusinessLinePathMixin,
    DetailView
):
    model = BusinessLine
    template_name = 'business_lines/business_line_detail.html'
    context_object_name = 'business_line'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business_line = self.object
        context.update({
            'children_count': business_line.children.count(),
            'services_count': business_line.client_services.count(),
            'is_management_view': True,
        })
        return context
