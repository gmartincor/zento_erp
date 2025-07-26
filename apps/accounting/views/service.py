from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.http import Http404

from apps.accounting.models import ClientService
from apps.accounting.forms.service_form_factory import ServiceFormFactory
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
        normalized_category = category.lower() if category else None
        
        renew_from_id = self.request.GET.get('renew_from')
        source_service = None
        if renew_from_id:
            try:
                source_service = ClientService.objects.select_related('client').get(
                    id=renew_from_id, is_active=True
                )
            except ClientService.DoesNotExist:
                pass
        
        kwargs.update({
            'user': self.request.user,
            'business_line': business_line,
            'category': normalized_category,
            'source_service': source_service
        })
        return kwargs
        
    def get_base_context(self):
        business_line, line_path, category = self.get_business_line_data()
        normalized_category = category.lower() if category else None
        context = {}
        context.update(self.get_business_line_context(line_path, category))
        context.update({
            'business_line': business_line,
            'category': normalized_category,
            'current_category': category,
            'category_display': self.get_category_display_name(normalized_category),
            'back_url': reverse('accounting:category-services', 
                              kwargs={'line_path': line_path, 'category': category}),
        })
        return context


class ServiceCategoryListView(BaseServiceView, ListView):
    template_name = 'accounting/service_category_list.html'
    context_object_name = 'services'
    paginate_by = 25
    
    def get_queryset(self):
        from ..services.enhanced_filter_service import EnhancedFilterService
        from apps.core.constants import SERVICE_CATEGORIES
        
        business_line, _, category = self.get_business_line_data()
        
        category_value = None
        if category:
            category_key = category.upper()
            category_value = SERVICE_CATEGORIES.get(category_key)
        
        filters = {
            'status': self.request.GET.get('status'),
            'operational_status': self.request.GET.get('operational_status'),
            'payment_status': self.request.GET.get('payment_status'),
            'renewal_status': self.request.GET.get('renewal_status'),
            'client': self.request.GET.get('client'),
        }
        
        # Filtrar valores vacíos
        filters = {k: v for k, v in filters.items() if v}
        
        queryset = ClientService.objects.get_services_by_category_including_descendants(
            business_line, category_value
        )

        queryset = EnhancedFilterService.apply_filters(queryset, filters)
        
        return queryset.select_related('client', 'business_line').prefetch_related('payments')
    
    def get_context_data(self, **kwargs):
        from ..services.enhanced_filter_service import EnhancedFilterService
        from ..services.presentation_service import PresentationService
        
        context = super().get_context_data(**kwargs)
        business_line, line_path, category = self.get_business_line_data()
        normalized_category = category.upper() if category else None
        
        view_mode = self.request.GET.get('view', 'list')
        if view_mode not in ['grid', 'list']:
            view_mode = 'list'
        
        filters = {
            'status': self.request.GET.get('status'),
            'operational_status': self.request.GET.get('operational_status'),
            'payment_status': self.request.GET.get('payment_status'),
            'renewal_status': self.request.GET.get('renewal_status'),
            'client': self.request.GET.get('client'),
        }
        filters = {k: v for k, v in filters.items() if v}
        
        category_context = self.get_service_category_context(business_line, category)
        
        presentation_service = PresentationService()
        period_type = self.request.GET.get('period', 'all_time')
        revenue_summary = presentation_service.prepare_category_revenue_summary(
            business_line, category.lower(), period_type
        )
        
        available_periods = [
            ('current_month', 'Mes actual'),
            ('last_month', 'Mes anterior'), 
            ('current_year', 'Año actual'),
            ('last_year', 'Año anterior'),
            ('last_3_months', 'Últimos 3 meses'),
            ('last_6_months', 'Últimos 6 meses'),
            ('last_12_months', 'Últimos 12 meses'),
            ('all_time', 'Histórico total'),
        ]
        
        context.update(self.get_base_context())
        context.update(category_context)
        context.update({
            'business_line': business_line,
            'category': normalized_category,
            'page_title': f'Servicios - {business_line.name}',
            'applied_filters': filters,
            'filter_summary': EnhancedFilterService.get_active_filters(dict(self.request.GET)),
            'active_filters_count': len(EnhancedFilterService.get_active_filters(dict(self.request.GET))),
            'filter_conflicts': EnhancedFilterService.detect_conflicts(dict(self.request.GET)),
            'revenue_summary': revenue_summary,
            'available_periods': available_periods,
            'selected_period': period_type,
        })
        
        context.update({
            'line_detail_url': reverse('accounting:business-lines-path', 
                                     kwargs={'line_path': line_path}),
            'create_url': reverse('accounting:service-create',
                                kwargs={'line_path': line_path, 'category': category}),
            'view_mode': view_mode,
        })
        
        return context


class ServiceEditView(BaseServiceView, UpdateView):
    template_name = 'accounting/service_edit.html'
    
    def get_form_class(self):
        business_line, _, category = self.get_business_line_data()
        normalized_category = category.lower() if category else None
        return ServiceFormFactory.get_update_form(normalized_category)
    
    def get_object(self):
        service = get_object_or_404(
            ClientService.objects.select_related('client', 'business_line'),
            id=self.kwargs['service_id']
        )
        
        self.check_business_line_permission(service.business_line)
        business_line, _, category = self.get_business_line_data()
        normalized_category = category.lower() if category else None
        
        if service.business_line != business_line or service.category != normalized_category:
            messages.error(self.request, 'Servicio no encontrado')
            raise Http404("Servicio no encontrado")
        
        service.get_fresh_service_data()
        return service
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.get_object()
        
        from ..services.service_progress_service import ServiceProgressService
        progress_data = ServiceProgressService.get_service_progress_data(service)
        
        context.update(self.get_base_context())
        context.update({
            'service': service,
            'page_title': f'Editar Servicio - {service.client.full_name}'
        })
        context.update(progress_data)
        
        return context
    
    def get_success_url(self):
        _, line_path, category = self.get_business_line_data()
        return reverse('accounting:category-services', 
                      kwargs={'line_path': line_path, 'category': category.lower()})
    
    def form_valid(self, form):
        try:
            service = form.save()
            service.get_fresh_service_data()
            self.object = service
            return redirect(self.get_success_url())
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
        normalized_category = category.lower() if category else None
        return ServiceFormFactory.get_create_form(normalized_category)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business_line, _, category = self.get_business_line_data()
        
        renew_from_id = self.request.GET.get('renew_from')
        source_service_info = None
        
        if renew_from_id:
            try:
                from apps.accounting.services.client_reactivation_service import ClientReactivationService
                source_service = ClientService.objects.select_related('client').get(
                    id=renew_from_id, is_active=True
                )
                client_status = ClientReactivationService.get_client_status(source_service.client)
                source_service_info = {
                    'service': source_service,
                    'client_status': client_status,
                    'is_reactivation': client_status['status'] == 'long_inactive'
                }
            except ClientService.DoesNotExist:
                pass
        
        context.update(self.get_base_context())
        context.update({
            'business_line': business_line,
            'category': category,
            'page_title': f'Crear Servicio - {business_line.name}',
            'source_service_info': source_service_info
        })
        
        return context
    
    def form_valid(self, form):
        business_line, _, category = self.get_business_line_data()
        
        normalized_category = category.lower()
        self.validate_category(normalized_category)
        
        form.instance.business_line = business_line
        form.instance.category = normalized_category
        
        try:
            service = form.save()
            self.object = service
            messages.success(
                self.request, 
                f'Servicio creado exitosamente para {service.client.full_name}. '
                f'Se ha creado el primer período de facturación. Ahora puedes procesarlo como pago.'
            )
            return redirect(self.get_success_url())
        except Exception as e:
            form.add_error(None, f'Error al crear el servicio: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_success_url(self):
        if hasattr(self, 'object') and self.object:
            return reverse('accounting:service-payment', kwargs={
                'service_id': self.object.id
            })
        
        _, line_path, category = self.get_business_line_data()
        return reverse('accounting:category-services', 
                      kwargs={'line_path': line_path, 'category': category.lower()})
