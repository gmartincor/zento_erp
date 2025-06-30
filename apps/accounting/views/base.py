from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import Http404
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from apps.business_lines.models import BusinessLine
from apps.accounting.models import Client, ClientService
from apps.accounting.utils import BusinessLineNavigator, ServiceStatisticsCalculator
from apps.accounting.services.service_state_manager import ServiceStateManager
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
    model = BusinessLine
    template_name = 'accounting/dashboard.html'
    context_object_name = 'business_lines'
    
    def get_queryset(self):
        return BusinessLineNavigator.get_root_lines_for_user(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        accessible_lines = self.get_allowed_business_lines()
        
        overall_stats = self._get_simplified_stats(accessible_lines)
        dashboard_cards = self._prepare_dashboard_cards(overall_stats)
        expiring_services = self._get_expiring_services(accessible_lines)
        service_stats = self._get_service_status_stats(accessible_lines)
        
        user_context = self._prepare_user_context()
        
        context.update({
            'page_title': 'Gestión de Ingresos',
            'overall_stats': overall_stats,
            'dashboard_cards': dashboard_cards,
            'expiring_services': expiring_services,
            'service_stats': service_stats,
            'user_context': user_context,
        })
        return context
    
    def _get_simplified_stats(self, accessible_lines):
        services = ClientService.objects.by_business_lines(accessible_lines)
        active_services = services.active()
        
        from apps.accounting.models import ServicePayment
        total_revenue = ServicePayment.objects.filter(
            client_service__in=active_services,
            status=ServicePayment.StatusChoices.PAID
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        unique_clients = active_services.values('client').distinct().count()
        
        return {
            'total_revenue': total_revenue,
            'total_services': active_services.count(),
            'unique_clients': unique_clients,
            'total_lines': accessible_lines.count()
        }
    
    def _get_expiring_services(self, accessible_lines):
        services = ClientService.objects.by_business_lines(accessible_lines)
        expiring = []
        
        for service in services:
            if ServiceStateManager.needs_renewal(service):
                expiring.append(service)
        
        return expiring[:10]
    
    def _get_service_status_stats(self, accessible_lines):
        from ..services.service_status_utility import ServiceStatusUtility
        return ServiceStatusUtility.get_status_counts(accessible_lines)
    
    def _prepare_dashboard_cards(self, stats):
        return [
            {
                'title': 'Ingresos Totales',
                'value': f"€{stats.get('total_revenue', 0):,.2f}",
                'icon': 'currency',
                'color': 'green',
                'description': 'Total de ingresos acumulados'
            },
            {
                'title': 'Servicios Activos', 
                'value': stats.get('total_services', 0),
                'icon': 'services',
                'color': 'blue',
                'description': 'Servicios actualmente activos'
            },
            {
                'title': 'Clientes Únicos',
                'value': stats.get('unique_clients', 0),
                'icon': 'users',
                'color': 'purple',
                'description': 'Clientes con servicios activos'
            },
            {
                'title': 'Líneas de Negocio',
                'value': stats.get('total_lines', 0),
                'icon': 'building',
                'color': 'indigo',
                'description': 'Líneas de negocio disponibles'
            }
        ]
    
    def _prepare_user_context(self):
        user = self.request.user
        return {
            'is_autonomo': user.role == 'AUTONOMO',
            'can_create_lines': True,
            'welcome_message': self._get_welcome_message(user),
            'available_actions': self._get_available_actions(user)
        }
    
    def _get_welcome_message(self, user):
        return 'Gestiona tus ingresos y servicios'
    
    def _get_available_actions(self, user):
        actions = []
        actions.append({
            'label': 'Nueva Línea',
            'url': '#',
            'icon': 'plus',
            'style': 'secondary'
        })
        actions.append({
            'label': 'Ver Reportes',
            'url': '#',
            'icon': 'chart',
            'style': 'primary'
        })
        return actions
