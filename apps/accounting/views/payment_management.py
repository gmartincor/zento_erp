from django.shortcuts import render
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta

from apps.accounting.models import ClientService, ServicePayment
from apps.accounting.services.service_state_manager import ServiceStateManager
from apps.accounting.services.payment_service import PaymentService
from apps.core.mixins import BusinessLinePermissionMixin


class PaymentManagementView(LoginRequiredMixin, BusinessLinePermissionMixin, ListView):
    model = ServicePayment
    template_name = 'accounting/payments/payment_management.html'
    context_object_name = 'payments'
    paginate_by = 25
    
    def get_queryset(self):
        accessible_lines = self.get_allowed_business_lines()
        
        queryset = ServicePayment.objects.filter(
            client_service__business_line__in=accessible_lines
        ).select_related('client_service__client', 'client_service__business_line').order_by('-payment_date')
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(client_service__client__full_name__icontains=search) |
                Q(client_service__business_line__name__icontains=search)
            )
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        accessible_lines = self.get_allowed_business_lines()
        
        total_payments = self.get_queryset().aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        context.update({
            'total_amount': total_payments['total'] or 0,
            'total_count': total_payments['count'] or 0,
            'business_lines': accessible_lines,
            'status_choices': ServicePayment.StatusChoices.choices,
            'page_title': 'Gestión de Pagos',
        })
        
        return context


class ExpiringServicesView(LoginRequiredMixin, BusinessLinePermissionMixin, ListView):
    model = ClientService
    template_name = 'accounting/services/expiring_services.html'
    context_object_name = 'services'
    paginate_by = 25
    
    def get_queryset(self):
        accessible_lines = self.get_allowed_business_lines()
        days = int(self.request.GET.get('days', 30))
        
        services = []
        all_services = ClientService.services.filter(
            business_line__in=accessible_lines,
            is_active=True
        ).select_related('client', 'business_line').prefetch_related('payments')
        
        for service in all_services:
            active_until = PaymentService.get_service_active_until(service)
            if active_until:
                days_left = (active_until - timezone.now().date()).days
                if 0 <= days_left <= days:
                    services.append(service.pk)
        
        return all_services.filter(pk__in=services).order_by('created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        services_with_status = []
        for service in context['services']:
            status = ServiceStateManager.get_service_status(service)
            active_until = PaymentService.get_service_active_until(service)
            days_left = None
            if active_until:
                days_left = (active_until - timezone.now().date()).days
                
            services_with_status.append({
                'service': service,
                'status': status,
                'status_display': ServiceStateManager.get_status_display(status),
                'active_until': active_until,
                'days_left': days_left
            })
        
        context.update({
            'services_with_status': services_with_status,
            'days_filter': int(self.request.GET.get('days', 30)),
            'page_title': 'Servicios Próximos a Vencer',
        })
        
        return context
