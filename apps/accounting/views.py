"""
Views for the accounting module.
Hierarchical navigation through business lines with permission control.
"""

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
        
        context.update({
            'page_title': 'Gestión de Ingresos',
            'overall_stats': overall_stats,
            'user_role': self.request.user.role,
        })
        
        return context


class BusinessLineDetailView(
    LoginRequiredMixin, 
    BusinessLinePermissionMixin, 
    BusinessLineHierarchyMixin,
    DetailView
):
    """
    Detail view for a specific business line.
    Shows children lines or category options if it's a leaf node.
    """
    model = BusinessLine
    template_name = 'accounting/business_line_detail.html'
    context_object_name = 'business_line'
    
    def get_object(self):
        """Get business line from hierarchical path."""
        line_path = self.kwargs.get('line_path', '')
        business_line = self.resolve_business_line_from_path(line_path)
        
        # Check permissions
        self.check_business_line_permission(business_line)
        
        return business_line
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business_line = self.get_object()
        
        # Get hierarchy context
        line_path = self.kwargs.get('line_path', '')
        hierarchy_context = self.get_business_line_context(line_path)
        context.update(hierarchy_context)
        
        # Get children or category statistics
        children = BusinessLineNavigator.get_children_for_display(
            business_line, 
            self.get_allowed_business_lines()
        )
        
        # Calculate statistics for this line
        line_stats = ServiceStatisticsCalculator.calculate_business_line_stats(
            business_line, 
            include_children=True
        )
        
        # Get category-specific stats if it's a leaf node
        category_stats = {}
        if not children.exists():
            for category in SERVICE_CATEGORIES.keys():
                category_stats[category] = ServiceStatisticsCalculator.calculate_business_line_stats(
                    business_line, 
                    include_children=False
                )
        
        context.update({
            'children': children,
            'line_stats': line_stats,
            'category_stats': category_stats,
            'is_leaf_node': not children.exists(),
            'service_categories': SERVICE_CATEGORIES,
        })
        
        return context


class ServiceCategoryListView(
    LoginRequiredMixin,
    BusinessLinePermissionMixin,
    BusinessLineHierarchyMixin,
    ServiceCategoryMixin,
    ListView
):
    """
    List view for services in a specific category (WHITE/BLACK) within a business line.
    Provides inline editing capabilities and statistics.
    """
    model = ClientService
    template_name = 'accounting/service_category_list.html'
    context_object_name = 'services'
    paginate_by = 25
    
    def get_queryset(self):
        """Get services filtered by business line and category."""
        business_line = self.get_business_line()
        category = self.get_category()
        
        return self.get_services_by_category(business_line, category)
    
    def get_business_line(self):
        """Get business line from path and check permissions."""
        line_path = self.kwargs.get('line_path', '')
        business_line = self.resolve_business_line_from_path(line_path)
        self.check_business_line_permission(business_line)
        return business_line
    
    def get_category(self):
        """Get and validate category from URL."""
        category = self.kwargs.get('category', '').upper()
        self.validate_category(category)
        return category
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        business_line = self.get_business_line()
        category = self.get_category()
        line_path = self.kwargs.get('line_path', '')
        
        # Get hierarchy context
        hierarchy_context = self.get_business_line_context(line_path, category)
        context.update(hierarchy_context)
        
        # Get category-specific context
        category_context = self.get_service_category_context(business_line, category)
        context.update(category_context)
        
        # Get category counts for tabs
        category_counts = self.get_category_counts(business_line)
        context.update(category_counts)
        
        # Add URLs for actions
        context.update({
            'create_url': reverse('accounting:service-create', 
                                kwargs={'line_path': line_path, 'category': category.lower()}),
            'line_detail_url': reverse('accounting:line-detail', 
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
    """
    Edit view for services with integrated client editing.
    Handles both service and client data in a single form.
    """
    model = ClientService
    template_name = 'accounting/service_edit.html'
    fields = ['client', 'price', 'start_date', 'end_date', 'payment_method', 'notes']
    
    def get_object(self):
        """Get service object and validate permissions."""
        service = get_object_or_404(
            ClientService.objects.select_related('client', 'business_line'),
            id=self.kwargs['service_id'],
            is_active=True
        )
        
        # Check business line permission
        self.check_business_line_permission(service.business_line)
        
        # Validate that the service belongs to the correct line and category
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
        
        # Get hierarchy context
        hierarchy_context = self.get_business_line_context(line_path, category.upper())
        context.update(hierarchy_context)
        
        # Add service-specific context
        context.update({
            'service': service,
            'client': service.client,
            'category_display': self.get_category_display_name(category.upper()),
            'back_url': reverse('accounting:category-services', 
                              kwargs={'line_path': line_path, 'category': category}),
        })
        
        return context
    
    def get_success_url(self):
        """Redirect back to category list after successful edit."""
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '')
        
        return reverse('accounting:category-services', 
                      kwargs={'line_path': line_path, 'category': category})
    
    def form_valid(self, form):
        """Handle successful form submission with success message."""
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            ACCOUNTING_SUCCESS_MESSAGES['SERVICE_UPDATED']
        )
        
        return response


class ServiceCreateView(
    LoginRequiredMixin,
    BusinessLinePermissionMixin,
    BusinessLineHierarchyMixin,
    ServiceCategoryMixin,
    CreateView
):
    """
    Create view for new services.
    Integrates client creation/selection with service creation.
    """
    model = ClientService
    template_name = 'accounting/service_create.html'
    fields = ['client', 'price', 'start_date', 'end_date', 'payment_method', 'notes']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '').upper()
        
        # Get business line and validate permissions
        business_line = self.resolve_business_line_from_path(line_path)
        self.check_business_line_permission(business_line)
        
        # Get hierarchy context
        hierarchy_context = self.get_business_line_context(line_path, category)
        context.update(hierarchy_context)
        
        # Add creation-specific context
        context.update({
            'business_line': business_line,
            'category': category,
            'category_display': self.get_category_display_name(category),
            'back_url': reverse('accounting:category-services', 
                              kwargs={'line_path': line_path, 'category': category.lower()}),
        })
        
        return context
    
    def form_valid(self, form):
        """Set business line and category before saving."""
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '').upper()
        
        # Get business line
        business_line = self.resolve_business_line_from_path(line_path)
        
        # Validate category
        self.validate_category(category)
        
        # Set the business line and category
        form.instance.business_line = business_line
        form.instance.category = category
        
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            ACCOUNTING_SUCCESS_MESSAGES['SERVICE_CREATED'].format(
                client=form.instance.client.full_name
            )
        )
        
        return response
    
    def get_success_url(self):
        """Redirect back to category list after successful creation."""
        line_path = self.kwargs.get('line_path', '')
        category = self.kwargs.get('category', '')
        
        return reverse('accounting:category-services', 
                      kwargs={'line_path': line_path, 'category': category})


class BusinessLineListView(LoginRequiredMixin, BusinessLinePermissionMixin, ListView):
    """
    Vista especializada que muestra todas las líneas de negocio accesibles al usuario
    con estadísticas consolidadas de ingresos, categorizadas y ordenadas jerárquicamente.
    
    Provides:
    - Comprehensive business line overview with revenue statistics
    - Hierarchical organization of business lines
    - Performance metrics by category (WHITE/BLACK)
    - Quick navigation to detailed views
    - Filter and search capabilities
    """
    model = BusinessLine
    template_name = 'accounting/business_line_list.html'
    context_object_name = 'business_lines'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Get all business lines accessible to the user with optimized queries.
        Includes revenue statistics and proper ordering.
        """
        # Get all accessible business lines
        accessible_lines = self.get_allowed_business_lines()
        
        # Apply search filter if provided
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            accessible_lines = accessible_lines.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(parent__name__icontains=search_query)
            )
        
        # Optimize with select_related and annotations
        queryset = accessible_lines.select_related('parent').prefetch_related(
            'children'
        ).annotate(
            # Annotate with service counts
            total_services=Count('client_services', filter=Q(client_services__is_active=True)),
            white_services=Count(
                'client_services', 
                filter=Q(client_services__is_active=True, client_services__category='WHITE')
            ),
            black_services=Count(
                'client_services', 
                filter=Q(client_services__is_active=True, client_services__category='BLACK')
            ),
            # Annotate with revenue sums
            total_revenue=Sum(
                'client_services__price', 
                filter=Q(client_services__is_active=True)
            ),
            white_revenue=Sum(
                'client_services__price',
                filter=Q(client_services__is_active=True, client_services__category='WHITE')
            ),
            black_revenue=Sum(
                'client_services__price',
                filter=Q(client_services__is_active=True, client_services__category='BLACK')
            )
        ).order_by('parent__name', 'name')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Enhanced context with comprehensive statistics and navigation aids."""
        context = super().get_context_data(**kwargs)
        
        # Get all accessible lines for global statistics
        accessible_lines = self.get_allowed_business_lines()
        
        # Calculate global statistics
        global_stats = ServiceStatisticsCalculator.get_revenue_summary_by_period(
            accessible_lines
        )
        
        # Calculate category-wise global statistics
        category_stats = {}
        for category_key, category_name in SERVICE_CATEGORIES.items():
            category_stats[category_key] = {
                'name': category_name,
                'total_services': accessible_lines.aggregate(
                    count=Count(
                        'client_services',
                        filter=Q(client_services__is_active=True, client_services__category=category_key)
                    )
                )['count'] or 0,
                'total_revenue': accessible_lines.aggregate(
                    revenue=Sum(
                        'client_services__price',
                        filter=Q(client_services__is_active=True, client_services__category=category_key)
                    )
                )['revenue'] or 0
            }
        
        # Get hierarchical organization for navigation
        root_lines = BusinessLineNavigator.get_root_lines_for_user(self.request.user)
        hierarchy_map = self._build_hierarchy_map(accessible_lines)
        
        # Prepare filter and pagination context
        search_query = self.request.GET.get('search', '')
        
        context.update({
            'page_title': 'Líneas de Negocio - Vista Consolidada',
            'global_stats': global_stats,
            'category_stats': category_stats,
            'root_lines': root_lines,
            'hierarchy_map': hierarchy_map,
            'search_query': search_query,
            'user_role': self.request.user.role,
            'service_categories': SERVICE_CATEGORIES,
            'total_lines_count': accessible_lines.count(),
            'has_search': bool(search_query),
        })
        
        return context
    
    def _build_hierarchy_map(self, business_lines):
        """
        Build a hierarchical map for enhanced navigation.
        Returns a dict mapping parent_id -> list of children.
        """
        hierarchy_map = {}
        
        for line in business_lines:
            parent_id = line.parent_id if line.parent_id else 'root'
            if parent_id not in hierarchy_map:
                hierarchy_map[parent_id] = []
            hierarchy_map[parent_id].append(line)
        
        return hierarchy_map


class BusinessLineHierarchyView(LoginRequiredMixin, BusinessLinePermissionMixin, BusinessLineHierarchyMixin, ListView):
    """
    Vista de navegación jerárquica por líneas de negocio.
    
    Proporciona navegación drill-down a través de la jerarquía:
    Nivel 1 → Nivel 2 → Nivel 3 → Categorías → Clientes
    
    URL Pattern: /accounting/hierarchy/[path]/
    Ejemplos:
    - /accounting/hierarchy/ → Nivel 1 (Glow, Jaén, Rubi)
    - /accounting/hierarchy/jaen/ → Nivel 2 (Pepe, NPV)
    - /accounting/hierarchy/jaen/pepe/ → Nivel 3 (VideoCall, Normal)
    - /accounting/hierarchy/jaen/pepe/normal/ → Categorías (BLACK, WHITE)
    - /accounting/hierarchy/jaen/pepe/normal/white/ → Clientes
    """
    model = BusinessLine
    template_name = 'accounting/hierarchy_navigation.html'
    context_object_name = 'items'
    
    def dispatch(self, request, *args, **kwargs):
        """Extraer y validar el path jerárquico de la URL"""
        self.line_path = kwargs.get('line_path', '').strip('/')
        self.path_segments = [seg for seg in self.line_path.split('/') if seg] if self.line_path else []
        self.navigation_level = len(self.path_segments)
        self.current_business_line = None
        
        # Validar y resolver la línea de negocio actual si existe path
        if self.line_path:
            try:
                self.current_business_line = self.resolve_business_line_from_path(self.line_path)
                self.enforce_business_line_permission(self.current_business_line)
            except Http404:
                # Si la línea no existe, redirigir al nivel superior
                if self.navigation_level > 1:
                    parent_path = '/'.join(self.path_segments[:-1])
                    return redirect('accounting:hierarchy-path', line_path=parent_path)
                else:
                    return redirect('accounting:hierarchy')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Obtener elementos del nivel actual de navegación"""
        accessible_lines = self.get_allowed_business_lines()
        
        if self.navigation_level == 0:
            # Nivel 1: Líneas padre (nivel 1)
            return accessible_lines.filter(level=1, parent=None).annotate(
                total_revenue=Sum('client_services__price', filter=Q(client_services__is_active=True)),
                total_services=Count('client_services', filter=Q(client_services__is_active=True)),
                children_count=Count('children', filter=Q(children__is_active=True))
            ).order_by('order', 'name')
            
        elif self.navigation_level == 1:
            # Nivel 2: Hijos de la línea seleccionada
            parent_line = self.current_business_line
            return accessible_lines.filter(parent=parent_line, level=2).annotate(
                total_revenue=Sum('client_services__price', filter=Q(client_services__is_active=True)),
                total_services=Count('client_services', filter=Q(client_services__is_active=True)),
                children_count=Count('children', filter=Q(children__is_active=True))
            ).order_by('order', 'name')
            
        elif self.navigation_level == 2:
            # Nivel 3: Hijos de segundo nivel, pero si no hay hijos, mostrar categorías
            parent_line = self.current_business_line
            sublevel_lines = accessible_lines.filter(parent=parent_line, level=3)
            
            if sublevel_lines.exists():
                # Hay sublíneas de nivel 3, mostrarlas
                return sublevel_lines.annotate(
                    total_revenue=Sum('client_services__price', filter=Q(client_services__is_active=True)),
                    total_services=Count('client_services', filter=Q(client_services__is_active=True)),
                    white_revenue=Sum('client_services__price', filter=Q(client_services__is_active=True, client_services__category='WHITE')),
                    black_revenue=Sum('client_services__price', filter=Q(client_services__is_active=True, client_services__category='BLACK'))
                ).order_by('order', 'name')
            else:
                # No hay sublíneas, mostrar categorías directamente
                categories_data = []
                
                for category in ['WHITE', 'BLACK']:
                    stats = ClientService.objects.filter(
                        business_line=parent_line,
                        category=category,
                        is_active=True
                    ).aggregate(
                        total_revenue=Sum('price'),
                        total_services=Count('id'),
                        unique_clients=Count('client', distinct=True)
                    )
                    
                    categories_data.append({
                        'category': category,
                        'name': 'Servicios Blancos' if category == 'WHITE' else 'Servicios Negros',
                        'total_revenue': stats['total_revenue'] or 0,
                        'total_services': stats['total_services'] or 0,
                        'unique_clients': stats['unique_clients'] or 0,
                        'avg_revenue': (stats['total_revenue'] / stats['total_services']) if stats['total_services'] else 0
                    })
                
                return categories_data
            
        elif self.navigation_level >= 3:
            # Manejar nivel de categorías y clientes de forma dinámica
            
            # Verificar si el último segmento es una categoría
            last_segment = self.path_segments[-1].upper() if self.path_segments else ''
            
            if last_segment in ['WHITE', 'BLACK']:
                # Estamos en vista de clientes - el penúltimo segmento determina la línea
                category = last_segment
                line_path_without_category = '/'.join(self.path_segments[:-1])
                business_line = self.resolve_business_line_from_path(line_path_without_category)
                
                return ClientService.objects.filter(
                    business_line=business_line,
                    category=category,
                    is_active=True
                ).select_related('client', 'business_line').annotate(
                    client_total_revenue=Sum('price')
                ).order_by('-client_total_revenue', 'client__full_name')
            else:
                # Estamos en vista de categorías (nivel 3)
                line = self.current_business_line
                categories_data = []
                
                for category in ['WHITE', 'BLACK']:
                    stats = ClientService.objects.filter(
                        business_line=line,
                        category=category,
                        is_active=True
                    ).aggregate(
                        total_revenue=Sum('price'),
                        total_services=Count('id'),
                        unique_clients=Count('client', distinct=True)
                    )
                    
                    categories_data.append({
                        'category': category,
                        'name': 'Servicios Blancos' if category == 'WHITE' else 'Servicios Negros',
                        'total_revenue': stats['total_revenue'] or 0,
                        'total_services': stats['total_services'] or 0,
                        'unique_clients': stats['unique_clients'] or 0,
                        'avg_revenue': (stats['total_revenue'] / stats['total_services']) if stats['total_services'] else 0
                    })
                
                return categories_data
        
        return BusinessLine.objects.none()
    
    def get_context_data(self, **kwargs):
        """Contexto enriquecido para navegación jerárquica"""
        context = super().get_context_data(**kwargs)
        
        # Información del nivel actual
        context.update({
            'navigation_level': self.navigation_level,
            'line_path': self.line_path,
            'path_segments': self.path_segments,
            'current_business_line': self.current_business_line,
        })
        
        # Breadcrumbs de navegación
        breadcrumbs = self._build_breadcrumbs()
        context['breadcrumbs'] = breadcrumbs
        
        # URL de retorno
        context['back_url'] = self._get_back_url()
        
        # Título y subtítulo según el nivel
        if self.navigation_level == 0:
            context.update({
                'page_title': 'Líneas de Negocio',
                'page_subtitle': 'Selecciona una línea de negocio para navegar',
                'view_type': 'business_lines'
            })
        elif self.navigation_level == 1:
            context.update({
                'page_title': f'Sublíneas de {self.current_business_line.name}',
                'page_subtitle': f'Nivel {self.navigation_level + 1} - Selecciona una sublínea',
                'view_type': 'business_lines'
            })
        elif self.navigation_level == 2:
            # Verificar si estamos mostrando sublíneas o categorías
            items = context.get('items', [])
            if items and hasattr(items[0], 'name'):
                # Estamos mostrando líneas de negocio (sublíneas)
                context.update({
                    'page_title': f'Sublíneas de {self.current_business_line.name}',
                    'page_subtitle': f'Nivel {self.navigation_level + 1} - Selecciona una sublínea',
                    'view_type': 'business_lines'
                })
            else:
                # Estamos mostrando categorías
                context.update({
                    'page_title': f'Categorías de {self.current_business_line.name}',
                    'page_subtitle': 'Selecciona una categoría para ver clientes',
                    'view_type': 'categories'
                })
        elif self.navigation_level >= 3:
            # Verificar si estamos viendo categorías o clientes
            last_segment = self.path_segments[-1].upper() if self.path_segments else ''
            
            if last_segment in ['WHITE', 'BLACK']:
                # Vista de clientes
                category_name = 'Servicios Blancos' if last_segment == 'WHITE' else 'Servicios Negros'
                line_name = self.current_business_line.name if self.current_business_line else 'Línea'
                context.update({
                    'page_title': f'Clientes - {category_name}',
                    'page_subtitle': f'{line_name} - Lista de clientes y servicios',
                    'view_type': 'clients',
                    'current_category': last_segment
                })
            else:
                # Vista de categorías
                context.update({
                    'page_title': f'Categorías de {self.current_business_line.name}',
                    'page_subtitle': 'Selecciona una categoría para ver clientes',
                    'view_type': 'categories'
                })
        
        # Estadísticas globales del nivel actual
        if self.navigation_level < 4:
            context['level_stats'] = self._calculate_level_stats()
        
        return context
    
    def _build_breadcrumbs(self):
        """Construir breadcrumbs de navegación"""
        breadcrumbs = [
            {'name': 'Ingresos', 'url': reverse('accounting:index')},
            {'name': 'Líneas de Negocio', 'url': reverse('accounting:hierarchy')}
        ]
        
        # Agregar breadcrumbs basados en el path actual
        current_path = ''
        hierarchy = self.get_hierarchy_path(self.current_business_line) if self.current_business_line else []
        
        for i, line in enumerate(hierarchy):
            if i < len(hierarchy) - 1:
                # Para elementos que no son el último, añadir con enlace
                current_path += line.slug
                breadcrumbs.append({
                    'name': line.name,
                    'url': reverse('accounting:hierarchy-path', kwargs={'line_path': current_path})
                })
                current_path += '/'
            else:
                # Último elemento (actual) sin enlace
                breadcrumbs.append({'name': line.name, 'url': None})
        
        # Si estamos en nivel de categorías o clientes, agregar categoría
        if self.navigation_level >= 3:
            if self.navigation_level == 4:
                category = self.path_segments[-1].upper()
                category_name = 'Servicios Blancos' if category == 'WHITE' else 'Servicios Negros'
                breadcrumbs.append({'name': category_name, 'url': None})
        
        return breadcrumbs
    
    def _get_back_url(self):
        """Calcular URL de retorno"""
        if self.navigation_level == 0:
            return reverse('accounting:index')
        elif self.navigation_level == 1:
            return reverse('accounting:hierarchy')
        else:
            parent_path = '/'.join(self.path_segments[:-1])
            return reverse('accounting:hierarchy-path', kwargs={'line_path': parent_path})
    
    def _calculate_level_stats(self):
        """Calcular estadísticas del nivel actual"""
        if self.navigation_level < 3:
            # Estadísticas de líneas de negocio
            queryset = self.get_queryset()
            # Verificar si es un QuerySet o una lista
            if hasattr(queryset, 'exists'):
                # Es un QuerySet
                if queryset.exists():
                    total_revenue = sum(getattr(item, 'total_revenue', 0) or 0 for item in queryset)
                    total_services = sum(getattr(item, 'total_services', 0) or 0 for item in queryset)
                    total_items = queryset.count()
                    
                    return {
                        'total_items': total_items,
                        'total_revenue': total_revenue,
                        'total_services': total_services,
                        'avg_revenue_per_line': total_revenue / total_items if total_items else 0
                    }
            else:
                # Es una lista (categorías)
                if queryset:
                    total_revenue = sum(cat.get('total_revenue', 0) or 0 for cat in queryset)
                    total_services = sum(cat.get('total_services', 0) or 0 for cat in queryset)
                    total_items = len(queryset)
                    
                    return {
                        'total_items': total_items,
                        'total_revenue': total_revenue,
                        'total_services': total_services,
                        'avg_revenue_per_line': total_revenue / total_items if total_items else 0
                    }
        elif self.navigation_level == 3:
            # Estadísticas de categorías
            categories = self.get_queryset()
            if categories:
                total_revenue = sum(cat.get('total_revenue', 0) or 0 for cat in categories)
                total_services = sum(cat.get('total_services', 0) or 0 for cat in categories)
                
                return {
                    'total_categories': len(categories),
                    'total_revenue': total_revenue,
                    'total_services': total_services,
                    'categories_breakdown': categories
                }
        
        return {}


class CategorySummaryView(LoginRequiredMixin, BusinessLinePermissionMixin, ListView):
    """
    Vista especializada para análisis consolidado por categorías (WHITE/BLACK).
    
    LEGACY VIEW - Para compatibilidad. Se recomienda usar la navegación jerárquica.
    """
    model = ClientService
    template_name = 'accounting/category_summary.html'
    context_object_name = 'services'
    paginate_by = 50
    
    def get_queryset(self):
        """Get all active services accessible to the user, optimized for category analysis."""
        accessible_lines = self.get_allowed_business_lines()
        
        queryset = ClientService.objects.filter(
            business_line__in=accessible_lines,
            is_active=True
        ).select_related('client', 'business_line', 'business_line__parent')
        
        # Apply category filter if provided
        category_filter = self.request.GET.get('category', '').upper()
        if category_filter in ['WHITE', 'BLACK']:
            queryset = queryset.filter(category=category_filter)
        
        return queryset.order_by('category', 'business_line__name', 'client__full_name')
    
    def get_context_data(self, **kwargs):
        """Enhanced context with comprehensive category analysis."""
        context = super().get_context_data(**kwargs)
        
        # Get accessible lines for calculations
        accessible_lines = self.get_allowed_business_lines()
        
        # Calculate global category statistics
        white_stats = self._calculate_category_stats('WHITE', accessible_lines)
        black_stats = self._calculate_category_stats('BLACK', accessible_lines)
        
        # Calculate category comparison metrics
        total_revenue = white_stats['total_revenue'] + black_stats['total_revenue']
        total_services = white_stats['total_services'] + black_stats['total_services']
        
        category_summary = {
            'total_categories': 2,
            'average_per_category': total_revenue / 2 if total_revenue > 0 else 0,
            'total_amount': total_revenue,
            'total_count': total_services
        }
        
        category_breakdown = [
            {
                'category_name': 'WHITE',
                'total_amount': white_stats['total_revenue'],
                'count': white_stats['total_services'],
                'avg_amount': white_stats['avg_price'],
                'percentage': (white_stats['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            },
            {
                'category_name': 'BLACK',
                'total_amount': black_stats['total_revenue'],
                'count': black_stats['total_services'],
                'avg_amount': black_stats['avg_price'],
                'percentage': (black_stats['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            }
        ]
        
        context.update({
            'page_title': 'Análisis por Categorías - WHITE vs BLACK',
            'subtitle': 'Análisis global de categorías',
            'category_summary': category_summary,
            'category_breakdown': category_breakdown,
        })
        
        return context
    
    def _calculate_category_stats(self, category, accessible_lines):
        """Calculate comprehensive statistics for a specific category."""
        services = ClientService.objects.filter(
            business_line__in=accessible_lines,
            category=category,
            is_active=True
        )
        
        stats = services.aggregate(
            total_revenue=Sum('price'),
            total_services=Count('id'),
            avg_price=Avg('price')
        )
        
        # Handle None values
        stats['total_revenue'] = stats['total_revenue'] or Decimal('0')
        stats['total_services'] = stats['total_services'] or 0
        stats['avg_price'] = stats['avg_price'] or Decimal('0')
        
        return stats


class ClientRevenueView(LoginRequiredMixin, BusinessLinePermissionMixin, ListView):
    """
    Vista para análisis de ingresos por cliente.
    
    LEGACY VIEW - Para compatibilidad. Se recomienda usar la navegación jerárquica.
    """
    template_name = 'accounting/client_revenue.html'
    context_object_name = 'client_revenue'
    paginate_by = 25
    
    def get_business_line(self):
        """Método requerido por algunas operaciones heredadas. Para análisis global, devuelve None."""
        return None
    
    def get_queryset(self):
        """Obtener servicios agrupados por cliente"""
        accessible_lines = self.get_allowed_business_lines()
        
        return ClientService.objects.filter(
            business_line__in=accessible_lines,
            is_active=True
        ).select_related('client', 'business_line').order_by('client__full_name', '-price')
    
    def get_context_data(self, **kwargs):
        """Enhanced context with client analysis."""
        context = super().get_context_data(**kwargs)
        
        # Get accessible lines for calculations
        accessible_lines = self.get_allowed_business_lines()
        
        # Calculate client summary
        client_summary = self.calculate_client_summary(accessible_lines)
        
        # Get client breakdown
        client_breakdown = self.calculate_client_breakdown(accessible_lines)
        
        # Get top clients
        top_clients = self.calculate_top_clients(accessible_lines)
        
        context.update({
            'page_title': 'Ingresos por Cliente',
            'subtitle': 'Análisis global de clientes',
            'client_summary': client_summary,
            'client_breakdown': client_breakdown,
            'top_clients': top_clients,
        })
        
        return context
    
    def calculate_client_summary(self, accessible_lines):
        """Calcular resumen general por cliente"""
        total_clients = (ClientService.objects
                        .filter(business_line__in=accessible_lines, is_active=True)
                        .values('client')
                        .distinct()
                        .count())
        
        total_amount = (ClientService.objects
                       .filter(business_line__in=accessible_lines, is_active=True)
                       .aggregate(total=Sum('price'))['total'] or Decimal('0'))
        
        avg_per_client = total_amount / total_clients if total_clients > 0 else Decimal('0')
        
        total_count = (ClientService.objects
                      .filter(business_line__in=accessible_lines, is_active=True)
                      .count())
        
        return {
            'total_clients': total_clients,
            'average_per_client': avg_per_client,
            'total_amount': total_amount,
            'total_count': total_count
        }
    
    def calculate_client_breakdown(self, accessible_lines):
        """Calcular desglose por cliente"""
        breakdown = (ClientService.objects
                    .filter(business_line__in=accessible_lines, is_active=True)
                    .values('client__id', 'client__full_name', 'client__email')
                    .annotate(
                        total_amount=Sum('price'),
                        count=Count('id'),
                        avg_amount=Avg('price')
                    )
                    .order_by('-total_amount'))
        
        total = sum(item['total_amount'] or Decimal('0') for item in breakdown)
        
        return [{
            'client_id': item['client__id'],
            'client_name': item['client__full_name'],
            'client_email': item['client__email'],
            'total_amount': item['total_amount'] or Decimal('0'),
            'count': item['count'],
            'avg_amount': item['avg_amount'] or Decimal('0'),
            'percentage': (item['total_amount'] / total * 100) if total > 0 else 0
        } for item in breakdown]
    
    def calculate_top_clients(self, accessible_lines, limit=10):
        """Calcular top clientes por ingresos"""
        top_clients = (ClientService.objects
                      .filter(business_line__in=accessible_lines, is_active=True)
                      .values('client__id', 'client__full_name')
                      .annotate(
                          total_amount=Sum('price'),
                          count=Count('id')
                      )
                      .order_by('-total_amount')[:limit])
        
        return [{
            'client_id': client['client__id'],
            'client_name': client['client__full_name'],
            'total_amount': client['total_amount'] or Decimal('0'),
            'count': client['count']
        } for client in top_clients]


class CategorySummaryView(LoginRequiredMixin, BusinessLinePermissionMixin, ListView):
    """
    Vista especializada para análisis consolidado por categorías (WHITE/BLACK).
    
    LEGACY VIEW - Para compatibilidad. Se recomienda usar la navegación jerárquica.
    """
    model = ClientService
    template_name = 'accounting/category_summary.html'
    context_object_name = 'services'
    paginate_by = 50
    
    def get_queryset(self):
        """Get all active services accessible to the user, optimized for category analysis."""
        accessible_lines = self.get_allowed_business_lines()
        
        queryset = ClientService.objects.filter(
            business_line__in=accessible_lines,
            is_active=True
        ).select_related('client', 'business_line', 'business_line__parent')
        
        # Apply category filter if provided
        category_filter = self.request.GET.get('category', '').upper()
        if category_filter in ['WHITE', 'BLACK']:
            queryset = queryset.filter(category=category_filter)
        
        return queryset.order_by('category', 'business_line__name', 'client__full_name')
    
    def get_context_data(self, **kwargs):
        """Enhanced context with comprehensive category analysis."""
        context = super().get_context_data(**kwargs)
        
        # Get accessible lines for calculations
        accessible_lines = self.get_allowed_business_lines()
        
        # Calculate global category statistics
        white_stats = self._calculate_category_stats('WHITE', accessible_lines)
        black_stats = self._calculate_category_stats('BLACK', accessible_lines)
        
        # Calculate category comparison metrics
        total_revenue = white_stats['total_revenue'] + black_stats['total_revenue']
        total_services = white_stats['total_services'] + black_stats['total_services']
        
        category_summary = {
            'total_categories': 2,
            'average_per_category': total_revenue / 2 if total_revenue > 0 else 0,
            'total_amount': total_revenue,
            'total_count': total_services
        }
        
        category_breakdown = [
            {
                'category_name': 'WHITE',
                'total_amount': white_stats['total_revenue'],
                'count': white_stats['total_services'],
                'avg_amount': white_stats['avg_price'],
                'percentage': (white_stats['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            },
            {
                'category_name': 'BLACK',
                'total_amount': black_stats['total_revenue'],
                'count': black_stats['total_services'],
                'avg_amount': black_stats['avg_price'],
                'percentage': (black_stats['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            }
        ]
        
        context.update({
            'page_title': 'Análisis por Categorías - WHITE vs BLACK',
            'subtitle': 'Análisis global de categorías',
            'category_summary': category_summary,
            'category_breakdown': category_breakdown,
        })
        
        return context
    
    def _calculate_category_stats(self, category, accessible_lines):
        """Calculate comprehensive statistics for a specific category."""
        services = ClientService.objects.filter(
            business_line__in=accessible_lines,
            category=category,
            is_active=True
        )
        
        stats = services.aggregate(
            total_revenue=Sum('price'),
            total_services=Count('id'),
            avg_price=Avg('price')
        )
        
        # Handle None values
        stats['total_revenue'] = stats['total_revenue'] or Decimal('0')
        stats['total_services'] = stats['total_services'] or 0
        stats['avg_price'] = stats['avg_price'] or Decimal('0')
        
        return stats


class ClientRevenueView(LoginRequiredMixin, BusinessLinePermissionMixin, ListView):
    """
    Vista para análisis de ingresos por cliente.
    
    LEGACY VIEW - Para compatibilidad. Se recomienda usar la navegación jerárquica.
    """
    template_name = 'accounting/client_revenue.html'
    context_object_name = 'client_revenue'
    paginate_by = 25
    
    def get_business_line(self):
        """Método requerido por algunas operaciones heredadas. Para análisis global, devuelve None."""
        return None
    
    def get_queryset(self):
        """Obtener servicios agrupados por cliente"""
        accessible_lines = self.get_allowed_business_lines()
        
        return ClientService.objects.filter(
            business_line__in=accessible_lines,
            is_active=True
        ).select_related('client', 'business_line').order_by('client__full_name', '-price')
    
    def get_context_data(self, **kwargs):
        """Enhanced context with client analysis."""
        context = super().get_context_data(**kwargs)
        
        # Get accessible lines for calculations
        accessible_lines = self.get_allowed_business_lines()
        
        # Calculate client summary
        client_summary = self.calculate_client_summary(accessible_lines)
        
        # Get client breakdown
        client_breakdown = self.calculate_client_breakdown(accessible_lines)
        
        # Get top clients
        top_clients = self.calculate_top_clients(accessible_lines)
        
        context.update({
            'page_title': 'Ingresos por Cliente',
            'subtitle': 'Análisis global de clientes',
            'client_summary': client_summary,
            'client_breakdown': client_breakdown,
            'top_clients': top_clients,
        })
        
        return context
    
    def calculate_client_summary(self, accessible_lines):
        """Calcular resumen general por cliente"""
        total_clients = (ClientService.objects
                        .filter(business_line__in=accessible_lines, is_active=True)
                        .values('client')
                        .distinct()
                        .count())
        
        total_amount = (ClientService.objects
                       .filter(business_line__in=accessible_lines, is_active=True)
                       .aggregate(total=Sum('price'))['total'] or Decimal('0'))
        
        avg_per_client = total_amount / total_clients if total_clients > 0 else Decimal('0')
        
        total_count = (ClientService.objects
                      .filter(business_line__in=accessible_lines, is_active=True)
                      .count())
        
        return {
            'total_clients': total_clients,
            'average_per_client': avg_per_client,
            'total_amount': total_amount,
            'total_count': total_count
        }
    
    def calculate_client_breakdown(self, accessible_lines):
        """Calcular desglose por cliente"""
        breakdown = (ClientService.objects
                    .filter(business_line__in=accessible_lines, is_active=True)
                    .values('client__id', 'client__full_name', 'client__email')
                    .annotate(
                        total_amount=Sum('price'),
                        count=Count('id'),
                        avg_amount=Avg('price')
                    )
                    .order_by('-total_amount'))
        
        total = sum(item['total_amount'] or Decimal('0') for item in breakdown)
        
        return [{
            'client_id': item['client__id'],
            'client_name': item['client__full_name'],
            'client_email': item['client__email'],
            'total_amount': item['total_amount'] or Decimal('0'),
            'count': item['count'],
            'avg_amount': item['avg_amount'] or Decimal('0'),
            'percentage': (item['total_amount'] / total * 100) if total > 0 else 0
        } for item in breakdown]
    
    def calculate_top_clients(self, accessible_lines, limit=10):
        """Calcular top clientes por ingresos"""
        top_clients = (ClientService.objects
                      .filter(business_line__in=accessible_lines, is_active=True)
                      .values('client__id', 'client__full_name')
                      .annotate(
                          total_amount=Sum('price'),
                          count=Count('id')
                      )
                      .order_by('-total_amount')[:limit])
        
        return [{
            'client_id': client['client__id'],
            'client_name': client['client__full_name'],
            'total_amount': client['total_amount'] or Decimal('0'),
            'count': client['count']
        } for client in top_clients]
