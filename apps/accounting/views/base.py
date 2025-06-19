"""
Base views and common utilities for accounting module.
Contains the main dashboard view and shared functionality.
"""

# Django core imports
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

# Local app imports
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
        
        # Prepare dashboard cards data (move logic from template)
        dashboard_cards = self._prepare_dashboard_cards(overall_stats)
        
        # User context for template logic
        user_context = self._prepare_user_context()
        
        context.update({
            'page_title': 'Gestión de Ingresos',
            'overall_stats': overall_stats,
            'dashboard_cards': dashboard_cards,
            'user_context': user_context,
        })
        
        return context
    
    def _prepare_dashboard_cards(self, stats):
        """Prepare dashboard cards data to avoid template logic."""
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
        """Prepare user context to avoid template logic."""
        user = self.request.user
        return {
            'is_admin': user.role == 'ADMIN',
            'is_glow_viewer': user.role == 'GLOW_VIEWER',
            'can_create_lines': user.role == 'ADMIN',
            'welcome_message': self._get_welcome_message(user),
            'available_actions': self._get_available_actions(user)
        }
    
    def _get_welcome_message(self, user):
        """Get personalized welcome message."""
        messages = {
            'ADMIN': 'Administra todos los ingresos y servicios del sistema',
            'GLOW_VIEWER': 'Gestiona los ingresos de tus líneas de negocio asignadas',
        }
        return messages.get(user.role, 'Panel de ingresos y servicios')
    
    def _get_available_actions(self, user):
        """Get available actions for the user."""
        actions = []
        
        if user.role == 'ADMIN':
            actions.append({
                'label': 'Nueva Línea',
                'url': '#',  # TODO: Add actual URL
                'icon': 'plus',
                'style': 'secondary'
            })
        
        actions.append({
            'label': 'Ver Reportes',
            'url': '#',  # TODO: Add actual URL
            'icon': 'chart',
            'style': 'primary'
        })
        
        return actions
