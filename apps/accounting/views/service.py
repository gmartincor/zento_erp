from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.http import Http404

from apps.accounting.models import Client, ClientService
from apps.accounting.forms.service_forms import ClientServiceCreateForm, ClientServiceUpdateForm
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


class ServiceCategoryListView(
    LoginRequiredMixin,
    BusinessLinePermissionMixin,
    BusinessLineHierarchyMixin,
    ServiceCategoryMixin,
    ListView
):
    model = ClientService
    template_name = 'accounting/service_category_list.html'
    context_object_name = 'services'
    paginate_by = 25
    
    def get_queryset(self):
        business_line = self.get_business_line()
        category = self.get_category()
        
        return self.get_services_by_category(business_line, category)
    
    def get_business_line(self):
        line_path = self.kwargs.get('line_path', '')
        business_line = self.resolve_business_line_from_path(line_path)
        self.check_business_line_permission(business_line)
        return business_line
    
    def get_category(self):
        category = self.kwargs.get('category', '').upper()
        self.validate_category(category)
        return category
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        business_line = self.get_business_line()
        category = self.get_category()
        line_path = self.kwargs.get('line_path', '')
        
        hierarchy_context = self.get_business_line_context(line_path, category)
        context.update(hierarchy_context)
        
        category_context = self.get_service_category_context(business_line, category)
        context.update(category_context)
        
        category_counts = self.get_category_counts(business_line)
        context.update(category_counts)
        
        context.update({
            'create_url': reverse('accounting:service-create', 
                                kwargs={'line_path': line_path, 'category': category.lower()}),
            'line_detail_url': reverse('accounting:business-lines-path', 
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
    model = ClientService
    form_class = ClientServiceUpdateForm
    template_name = 'accounting/service_edit.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '').upper()
        
        business_line = self.resolve_business_line_from_path(line_path)
        
        kwargs.update({
            'user': self.request.user,
            'business_line': business_line,
            'category': category
        })
        return kwargs
    
    def get_object(self):
        service = get_object_or_404(
            ClientService.objects.select_related('client', 'business_line'),
            id=self.kwargs['service_id'],
            is_active=True
        )
        
        self.check_business_line_permission(service.business_line)
        
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
        
        hierarchy_context = self.get_business_line_context(line_path, category.upper())
        context.update(hierarchy_context)
        
        context.update({
            'service': service,
            'client': service.client,
            'category_display': self.get_category_display_name(category.upper()),
            'back_url': reverse('accounting:category-services', 
                              kwargs={'line_path': line_path, 'category': category}),
        })
        
        return context
    
    def get_success_url(self):
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '')
        
        return reverse('accounting:category-services', 
                      kwargs={'line_path': line_path, 'category': category})
    
    def form_valid(self, form):
        try:
            self.object = form.save()
            
            messages.success(
                self.request,
                ACCOUNTING_SUCCESS_MESSAGES.get('SERVICE_UPDATED', 'Servicio actualizado correctamente.')
            )
            
            return redirect(self.get_success_url())
            
        except Exception as e:
            form.add_error(None, f'Error al actualizar el servicio: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request, 
            'Por favor, corrige los errores en el formulario.'
        )
        return super().form_invalid(form)


class ServiceCreateView(
    LoginRequiredMixin,
    BusinessLinePermissionMixin,
    BusinessLineHierarchyMixin,
    ServiceCategoryMixin,
    CreateView
):
    model = ClientService
    form_class = ClientServiceCreateForm
    template_name = 'accounting/service_create.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '').upper()
        
        business_line = self.resolve_business_line_from_path(line_path)
        
        kwargs.update({
            'user': self.request.user,
            'business_line': business_line,
            'category': category
        })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '').upper()
        
        business_line = self.resolve_business_line_from_path(line_path)
        self.check_business_line_permission(business_line)
        
        hierarchy_context = self.get_business_line_context(line_path, category)
        context.update(hierarchy_context)
        
        context.update({
            'business_line': business_line,
            'category': category,
            'category_display': self.get_category_display_name(category),
            'back_url': reverse('accounting:category-services', 
                              kwargs={'line_path': line_path, 'category': category.lower()}),
        })
        
        return context
    
    def form_valid(self, form):
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '').upper()
        
        business_line = self.resolve_business_line_from_path(line_path)
        
        self.validate_category(category)
        
        form.cleaned_data['business_line'] = business_line
        form.cleaned_data['category'] = category
        
        try:
            self.object = form.save()
            
            messages.success(
                self.request,
                ACCOUNTING_SUCCESS_MESSAGES.get('SERVICE_CREATED', 'Servicio creado correctamente para {client}').format(
                    client=self.object.client.full_name
                )
            )
            
            messages.info(
                self.request,
                'Ahora puedes agregar el primer pago para activar el servicio.'
            )
            
            return redirect(self.get_success_url())
            
        except Exception as e:
            form.add_error(None, f'Error al crear el servicio: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Por favor, corrige los errores en el formulario.'
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        if hasattr(self, 'object') and self.object:
            return reverse('accounting:payment_create', 
                          kwargs={'service_id': self.object.id})
        
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '')
        
        return reverse('accounting:category-services', 
                      kwargs={'line_path': line_path, 'category': category})
