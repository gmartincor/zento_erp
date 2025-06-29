from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.http import Http404
from django.contrib import messages

from apps.accounting.models import Client, ClientService
from apps.accounting.services.service_state_manager import ServiceStateManager
from apps.accounting.services.payment_service import PaymentService
from apps.accounting.services.history_service import HistoryService
from apps.core.mixins import BusinessLinePermissionMixin


class ClientServiceHistoryView(LoginRequiredMixin, BusinessLinePermissionMixin, ListView):
    model = ClientService
    template_name = 'accounting/client_service_history.html'
    context_object_name = 'services'
    paginate_by = 20
    
    def get_client(self):
        if not hasattr(self, '_client'):
            self._client = get_object_or_404(Client, id=self.kwargs['client_id'])
        return self._client
    
    def get_queryset(self):
        client = self.get_client()
        accessible_lines = self.get_allowed_business_lines()
        
        filters = {
            'is_active': self.request.GET.get('is_active'),
            'category': self.request.GET.get('category')
        }
        
        queryset = HistoryService.get_client_services_history(
            client.id, 
            {k: v for k, v in filters.items() if v}
        )
        
        return queryset.filter(business_line__in=accessible_lines)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_client()
        accessible_lines = self.get_allowed_business_lines()
        
        from ..services.service_status_utility import ServiceStatusUtility
        services_with_status = ServiceStatusUtility.get_services_with_status_data(context['services'])
        
        categories = ClientService.CategoryChoices.choices
        status_options = [('true', 'Activos'), ('false', 'Inactivos')]
        
        context.update({
            'client': client,
            'services_with_status': services_with_status,
            'categories': categories,
            'status_options': status_options,
            'available_business_lines': accessible_lines,
            'filter_params': {
                'is_active': self.request.GET.get('is_active'),
                'category': self.request.GET.get('category'),
            },
            'summary_stats': HistoryService.get_history_summary(client_id=client.id),
            'selected_is_active': self.request.GET.get('is_active'),
            'selected_category': self.request.GET.get('category'),
            'page_title': f'Historial de Servicios - {client.full_name}',
            'page_subtitle': f'Servicios contratados por {client.full_name}',
        })
        
        return context


class ClientServiceDetailView(LoginRequiredMixin, BusinessLinePermissionMixin, DetailView):
    model = ClientService
    template_name = 'accounting/client_service_detail.html'
    context_object_name = 'service'
    
    def get_object(self):
        service = get_object_or_404(
            ClientService.objects.select_related('client', 'business_line')
                                  .prefetch_related('payments'),
            id=self.kwargs['service_id']
        )
        
        self.check_business_line_permission(service.business_line)
        return service
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.object
        
        service_status = ServiceStateManager.get_service_status(service)
        payments = service.payments.order_by('-payment_date')
        
        context.update({
            'service_status': service_status,
            'status_display': ServiceStateManager.get_status_display(service_status),
            'payments': payments,
            'page_title': f'Detalle del Servicio - {service.client.full_name}',
            'page_subtitle': f'{service.business_line.name} • {service.get_category_display()}',
            'back_url': reverse('accounting:client-service-history', 
                              kwargs={'client_id': service.client.id}),
        })
        
        return context
