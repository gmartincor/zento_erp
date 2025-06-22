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
        overall_stats = ServiceStatisticsCalculator.get_revenue_summary_by_period(
            accessible_lines
        )
        dashboard_cards = self._prepare_dashboard_cards(overall_stats)
        user_context = self._prepare_user_context()
        context.update({
            'page_title': 'Gestión de Ingresos',
            'overall_stats': overall_stats,
            'dashboard_cards': dashboard_cards,
            'user_context': user_context,
        })
        return context
    
    def _prepare_dashboard_cards(self, stats):
        return [
            {
                'title': 'Ingresos Totales',
                'value': f"€{stats.get('total_revenue', 0):,.2f}",
                'icon': 'currency',
                'color': 'green',
                'description': 'Total de ingresos del período'
            },
            {
                'title': 'Servicios Activos', 
                'value': stats.get('total_services', 0),
                'icon': 'services',
                'color': 'blue',
                'description': 'Servicios actualmente en funcionamiento'
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
                'value': self.get_allowed_business_lines().count(),
                'icon': 'building',
                'color': 'indigo',
                'description': 'Líneas de negocio accesibles'
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
