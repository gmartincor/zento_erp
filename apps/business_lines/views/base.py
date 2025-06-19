"""
Base Views and Mixins - Business Line Management Foundation

Simple mixins for business line management without complex inheritance.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.urls import reverse


class AdminRequiredMixin:
    """
    Simple ADMIN role check.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Check ADMIN role before allowing access."""
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        if getattr(request.user, 'role', None) != 'ADMIN':
            raise PermissionDenied(
                "Solo los administradores pueden gestionar líneas de negocio."
            )
        
        return super().dispatch(request, *args, **kwargs)


class BusinessLineManagementMixin(LoginRequiredMixin, AdminRequiredMixin):
    """
    Base mixin for business line management operations.
    """
    context_object_name = 'business_line'
    
    def get_context_data(self, **kwargs):
        """Add common management context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'page_section': 'management',
            'is_management': True,
        })
        return context


class BusinessLineNavigationMixin:
    """
    Simple navigation mixin.
    """
    
    def get_success_url(self):
        """Redirect to accounting business lines after successful operations."""
        return reverse('accounting:business-lines')


class BusinessLineFormMixin:
    """
    Simple form mixin.
    """
    
    def form_valid(self, form):
        """Handle successful form submission."""
        response = super().form_valid(form)
        
        action = getattr(self, 'action_name', 'guardada')
        messages.success(
            self.request,
            f'Línea de negocio "{self.object.name}" {action} exitosamente.'
        )
        
        return response


class BusinessLineDependencyMixin:
    """
    Simple dependency mixin.
    """
    pass
