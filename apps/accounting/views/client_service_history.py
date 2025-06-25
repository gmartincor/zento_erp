from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.http import Http404
from django.contrib import messages

from apps.accounting.models import Client, ClientService
from apps.accounting.services.service_context_manager import ServiceContextManager
from apps.accounting.services.service_history_manager import ServiceHistoryManager
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
        business_line_id = self.request.GET.get('business_line')
        category = self.request.GET.get('category')
        
        accessible_lines = self.get_allowed_business_lines()
        
        if business_line_id:
            try:
                business_line = accessible_lines.get(id=business_line_id)
            except:
                business_line = None
        else:
            business_line = None
            
        return ServiceHistoryManager.get_client_service_history(
            client=client,
            business_line=business_line,
            category=category,
            accessible_lines=accessible_lines
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_client()
        accessible_lines = self.get_allowed_business_lines()
        
        history_context = ServiceContextManager.get_client_history_context(
            client=client,
            services=self.get_queryset(),
            accessible_lines=accessible_lines,
            request=self.request
        )
        
        context.update(history_context)
        context.update({
            'client': client,
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
        
        detail_context = ServiceContextManager.get_service_detail_context(
            service=service,
            request=self.request
        )
        
        context.update(detail_context)
        context.update({
            'page_title': f'Detalle del Servicio - {service.client.full_name}',
            'page_subtitle': f'{service.business_line.name} • {service.get_category_display()}',
            'back_url': reverse('accounting:client-service-history', 
                              kwargs={'client_id': service.client.id}),
        })
        
        return context
