"""
Views for the accounting module.
Hierarchical navigation through business lines with permission control.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import Http404

from apps.business_lines.models import BusinessLine
from apps.accounting.models import Client, ClientService
from apps.accounting.utils import BusinessLineNavigator, ServiceStatisticsCalculator
from apps.core.mixins import (
    BusinessLinePermissionMixin,
    BusinessLineHierarchyMixin,
    ServiceCategoryMixin
)
from apps.core.constants import (
    ACCOUNTING_SUCCESS_MESSAGES,
    SERVICE_CATEGORIES
)


class AccountingDashboardView(LoginRequiredMixin, BusinessLinePermissionMixin, ListView):
    """
    Main dashboard for accounting module.
    Shows root business lines accessible to the user with statistics.
    """
    model = BusinessLine
    template_name = 'accounting/dashboard.html'
    context_object_name = 'business_lines'
    
    def get_queryset(self):
        """Get root business lines accessible to the current user."""
        return BusinessLineNavigator.get_root_lines_for_user(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate overall statistics for accessible lines
        accessible_lines = self.get_allowed_business_lines()
        overall_stats = ServiceStatisticsCalculator.get_revenue_summary_by_period(
            accessible_lines
        )
        
        context.update({
            'page_title': 'Gestión de Ingresos',
            'overall_stats': overall_stats,
            'user_role': self.request.user.role,
        })
        
        return context


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
        business_line = self.get_object()
        
        # Get hierarchy context
        line_path = self.kwargs.get('line_path', '')
        hierarchy_context = self.get_business_line_context(line_path)
        context.update(hierarchy_context)
        
        # Get children or category statistics
        children = BusinessLineNavigator.get_children_for_display(
            business_line, 
            self.get_allowed_business_lines()
        )
        
        # Calculate statistics for this line
        line_stats = ServiceStatisticsCalculator.calculate_business_line_stats(
            business_line, 
            include_children=True
        )
        
        # Get category-specific stats if it's a leaf node
        category_stats = {}
        if not children.exists():
            for category in SERVICE_CATEGORIES.keys():
                category_stats[category] = ServiceStatisticsCalculator.calculate_business_line_stats(
                    business_line, 
                    include_children=False
                )
        
        context.update({
            'children': children,
            'line_stats': line_stats,
            'category_stats': category_stats,
            'is_leaf_node': not children.exists(),
            'service_categories': SERVICE_CATEGORIES,
        })
        
        return context


class ServiceCategoryListView(
    LoginRequiredMixin,
    BusinessLinePermissionMixin,
    BusinessLineHierarchyMixin,
    ServiceCategoryMixin,
    ListView
):
    """
    List view for services in a specific category (WHITE/BLACK) within a business line.
    Provides inline editing capabilities and statistics.
    """
    model = ClientService
    template_name = 'accounting/service_category_list.html'
    context_object_name = 'services'
    paginate_by = 25
    
    def get_queryset(self):
        """Get services filtered by business line and category."""
        business_line = self.get_business_line()
        category = self.get_category()
        
        return self.get_services_by_category(business_line, category)
    
    def get_business_line(self):
        """Get business line from path and check permissions."""
        line_path = self.kwargs.get('line_path', '')
        business_line = self.resolve_business_line_from_path(line_path)
        self.check_business_line_permission(business_line)
        return business_line
    
    def get_category(self):
        """Get and validate category from URL."""
        category = self.kwargs.get('category', '').upper()
        self.validate_category(category)
        return category
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        business_line = self.get_business_line()
        category = self.get_category()
        line_path = self.kwargs.get('line_path', '')
        
        # Get hierarchy context
        hierarchy_context = self.get_business_line_context(line_path, category)
        context.update(hierarchy_context)
        
        # Get category-specific context
        category_context = self.get_service_category_context(business_line, category)
        context.update(category_context)
        
        # Add URLs for actions
        context.update({
            'create_url': reverse('accounting:service-create', 
                                kwargs={'line_path': line_path, 'category': category.lower()}),
            'line_detail_url': reverse('accounting:line-detail', 
                                     kwargs={'line_path': line_path}),
        })
        
        return context


class ServiceEditView(
    LoginRequiredMixin,
    BusinessLinePermissionMixin,
    BusinessLineHierarchyMixin,
    ServiceCategoryMixin,
    UpdateView
):
    """
    Edit view for services with integrated client editing.
    Handles both service and client data in a single form.
    """
    model = ClientService
    template_name = 'accounting/service_edit.html'
    fields = ['client', 'price', 'start_date', 'end_date', 'payment_method', 'notes']
    
    def get_object(self):
        """Get service object and validate permissions."""
        service = get_object_or_404(
            ClientService.objects.select_related('client', 'business_line'),
            id=self.kwargs['service_id'],
            is_active=True
        )
        
        # Check business line permission
        self.check_business_line_permission(service.business_line)
        
        # Validate that the service belongs to the correct line and category
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '').upper()
        
        expected_line = self.resolve_business_line_from_path(line_path)
        if service.business_line != expected_line:
            raise Http404("Servicio no encontrado en esta línea de negocio.")
        
        if service.category != category:
            raise Http404("Servicio no encontrado en esta categoría.")
        
        return service
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        service = self.get_object()
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '')
        
        # Get hierarchy context
        hierarchy_context = self.get_business_line_context(line_path, category.upper())
        context.update(hierarchy_context)
        
        # Add service-specific context
        context.update({
            'service': service,
            'client': service.client,
            'category_display': self.get_category_display_name(category.upper()),
            'back_url': reverse('accounting:category-services', 
                              kwargs={'line_path': line_path, 'category': category}),
        })
        
        return context
    
    def get_success_url(self):
        """Redirect back to category list after successful edit."""
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '')
        
        return reverse('accounting:category-services', 
                      kwargs={'line_path': line_path, 'category': category})
    
    def form_valid(self, form):
        """Handle successful form submission with success message."""
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            ACCOUNTING_SUCCESS_MESSAGES['SERVICE_UPDATED']
        )
        
        return response


class ServiceCreateView(
    LoginRequiredMixin,
    BusinessLinePermissionMixin,
    BusinessLineHierarchyMixin,
    ServiceCategoryMixin,
    CreateView
):
    """
    Create view for new services.
    Integrates client creation/selection with service creation.
    """
    model = ClientService
    template_name = 'accounting/service_create.html'
    fields = ['client', 'price', 'start_date', 'end_date', 'payment_method', 'notes']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '').upper()
        
        # Get business line and validate permissions
        business_line = self.resolve_business_line_from_path(line_path)
        self.check_business_line_permission(business_line)
        
        # Get hierarchy context
        hierarchy_context = self.get_business_line_context(line_path, category)
        context.update(hierarchy_context)
        
        # Add creation-specific context
        context.update({
            'business_line': business_line,
            'category': category,
            'category_display': self.get_category_display_name(category),
            'back_url': reverse('accounting:category-services', 
                              kwargs={'line_path': line_path, 'category': category.lower()}),
        })
        
        return context
    
    def form_valid(self, form):
        """Set business line and category before saving."""
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '').upper()
        
        # Get business line
        business_line = self.resolve_business_line_from_path(line_path)
        
        # Validate category
        self.validate_category(category)
        
        # Set the business line and category
        form.instance.business_line = business_line
        form.instance.category = category
        
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            ACCOUNTING_SUCCESS_MESSAGES['SERVICE_CREATED'].format(
                client=form.instance.client.full_name
            )
        )
        
        return response
    
    def get_success_url(self):
        """Redirect back to category list after successful creation."""
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '')
        
        return reverse('accounting:category-services', 
                      kwargs={'line_path': line_path, 'category': category})
