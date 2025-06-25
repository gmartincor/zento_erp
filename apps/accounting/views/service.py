from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.http import Http404

from apps.accounting.models import ClientService
from apps.accounting.forms.service_form_factory import ServiceFormFactory
from apps.accounting.services.service_context_manager import ServiceContextManager
from apps.accounting.services.service_workflow_manager import ServiceWorkflowManager
from apps.core.mixins import (
    BusinessLinePermissionMixin,
    BusinessLineHierarchyMixin,
    ServiceCategoryMixin
)


class BaseServiceView(
    LoginRequiredMixin,
    BusinessLinePermissionMixin,
    BusinessLineHierarchyMixin,
    ServiceCategoryMixin
):
    model = ClientService
    
    def get_business_line_data(self):
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '').lower()
        business_line = self.resolve_business_line_from_path(line_path)
        self.check_business_line_permission(business_line)
        return business_line, line_path, category
        
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        business_line, _, category = self.get_business_line_data()
        kwargs.update({
            'user': self.request.user,
            'business_line': business_line,
            'category': category
        })
        return kwargs
        
    def get_base_context(self):
        business_line, line_path, category = self.get_business_line_data()
        context = {}
        context.update(self.get_business_line_context(line_path, category))
        context.update({
            'business_line': business_line,
            'category': category,
            'current_category': category,
            'category_display': self.get_category_display_name(category),
            'back_url': reverse('accounting:category-services', 
                              kwargs={'line_path': line_path, 'category': category}),
        })
        return context


class ServiceCategoryListView(BaseServiceView, ListView):
    template_name = 'accounting/service_category_list.html'
    context_object_name = 'services'
    paginate_by = 25
    
    def get_queryset(self):
        business_line, _, category = self.get_business_line_data()
        return self.get_services_by_category(business_line, category)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business_line, line_path, category = self.get_business_line_data()
        
        context.update(self.get_base_context())
        context.update(ServiceContextManager.get_service_creation_context(business_line, category))
        
        context.update({
            'line_detail_url': reverse('accounting:business-lines-path', 
                                     kwargs={'line_path': line_path}),
            'create_url': reverse('accounting:service-create',
                                kwargs={'line_path': line_path, 'category': category}),
        })
        
        return context


class ServiceEditView(BaseServiceView, UpdateView):
    template_name = 'accounting/service_edit.html'
    
    def get_form_class(self):
        business_line, _, category = self.get_business_line_data()
        return ServiceFormFactory.get_update_form(category)
    
    def get_object(self):
        service = get_object_or_404(
            ClientService.objects.select_related('client', 'business_line'),
            id=self.kwargs['service_id'],
            is_active=True
        )
        
        self.check_business_line_permission(service.business_line)
        business_line, _, category = self.get_business_line_data()
        
        if service.business_line != business_line or service.category != category:
            messages.error(self.request, 'Servicio no encontrado')
            raise Http404("Servicio no encontrado")
        
        return service
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.get_object()
        
        context.update(self.get_base_context())
        context.update(ServiceContextManager.get_service_edit_context(service))
        
        return context
    
    def get_success_url(self):
        _, line_path, category = self.get_business_line_data()
        return reverse('accounting:category-services', 
                      kwargs={'line_path': line_path, 'category': category.lower()})
    
    def form_valid(self, form):
        try:
            service, redirect_url = ServiceWorkflowManager.handle_service_update_flow(
                self.request, self.object, form.cleaned_data
            )
            self.object = service
            return redirect(redirect_url)
        except Exception as e:
            form.add_error(None, f'Error al actualizar el servicio: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)


class ServiceCreateView(BaseServiceView, CreateView):
    template_name = 'accounting/service_create.html'
    
    def get_form_class(self):
        business_line, _, category = self.get_business_line_data()
        return ServiceFormFactory.get_create_form(category)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business_line, _, category = self.get_business_line_data()
        
        context.update(self.get_base_context())
        context.update(ServiceContextManager.get_service_creation_context(business_line, category))
        
        return context
    
    def form_valid(self, form):
        business_line, _, category = self.get_business_line_data()
        
        self.validate_category(category)
        
        if not ServiceWorkflowManager.validate_service_creation_permissions(self.request.user, business_line):
            messages.error(self.request, 'No tienes permisos para crear servicios en esta línea de negocio.')
            return self.form_invalid(form)
        
        form.cleaned_data['business_line'] = business_line
        form.cleaned_data['category'] = category
        
        try:
            service, redirect_url = ServiceWorkflowManager.handle_service_creation_flow(
                self.request, form.cleaned_data, business_line, category
            )
            self.object = service
            return redirect(redirect_url)
        except Exception as e:
            form.add_error(None, f'Error al crear el servicio: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_success_url(self):
        if hasattr(self, 'object') and self.object:
            _, line_path, category = self.get_business_line_data()
            return reverse('accounting:service-edit', kwargs={
                'line_path': line_path, 
                'category': category.lower(),
                'service_id': self.object.id
            })
        
        _, line_path, category = self.get_business_line_data()
        return reverse('accounting:category-services', 
                      kwargs={'line_path': line_path, 'category': category.lower()})
