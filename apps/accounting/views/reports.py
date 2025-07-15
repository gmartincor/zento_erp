from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Avg, Q
from decimal import Decimal

from apps.accounting.models import ClientService, Client
from apps.accounting.utils import ServiceStatisticsCalculator
from apps.accounting.services.template_service import TemplateDataService
from apps.core.mixins import BusinessLinePermissionMixin
from apps.core.constants import SERVICE_CATEGORIES


class CategorySummaryView(LoginRequiredMixin, BusinessLinePermissionMixin, ListView):
    model = ClientService
    template_name = 'accounting/category_summary.html'
    context_object_name = 'services'
    paginate_by = 50
    
    def get_queryset(self):
        accessible_lines = self.get_allowed_business_lines()
        
        queryset = ClientService.objects.filter(
            business_line__in=accessible_lines,
            is_active=True
        ).select_related('client', 'business_line', 'business_line__parent')
        
        category_filter = self.request.GET.get('category', '').upper()
        if category_filter in [SERVICE_CATEGORIES['PERSONAL'], SERVICE_CATEGORIES['BUSINESS']]:
            queryset = queryset.filter(category=category_filter)
        
        return queryset.order_by('category', 'business_line__name', 'client__full_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        template_service = TemplateDataService()
        all_services = self.get_queryset()
        
        category_context = template_service.prepare_category_summary_context(all_services)
        context.update(category_context)
        
        category_filter = self.request.GET.get('category', '')
        context.update({
            'category_filter': category_filter,
            'page_title': f'Resumen por Categorías' + (f' - {category_filter}' if category_filter else ''),
            'subtitle': f'Análisis detallado de servicios por categoría'
        })
        
        return context


class ClientRevenueView(LoginRequiredMixin, BusinessLinePermissionMixin, ListView):
    model = ClientService
    template_name = 'accounting/client_revenue.html'
    context_object_name = 'services'
    paginate_by = 50
    
    def get_queryset(self):
        accessible_lines = self.get_allowed_business_lines()
        
        queryset = ClientService.objects.filter(
            business_line__in=accessible_lines,
            is_active=True
        ).select_related('client', 'business_line')
        
        client_filter = self.request.GET.get('client', '')
        if client_filter:
            queryset = queryset.filter(
                Q(client__full_name__icontains=client_filter) |
                Q(client__email__icontains=client_filter)
            )
        
        return queryset.order_by('client__full_name', '-amount')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        template_service = TemplateDataService()
        all_services = self.get_queryset()
        
        client_context = template_service.prepare_client_revenue_context(all_services)
        context.update(client_context)
        
        client_filter = self.request.GET.get('client', '')
        context.update({
            'client_filter': client_filter,
            'page_title': f'Ingresos por Cliente' + (f' - {client_filter}' if client_filter else ''),
            'subtitle': f'Análisis detallado de ingresos por cliente'
        })
        
        return context
