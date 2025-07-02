from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.http import Http404
from django.db.models import Q
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from apps.business_lines.models import BusinessLine
from apps.accounting.models import ClientService, ServicePayment
from apps.accounting.services.template_service import TemplateDataService
from apps.accounting.services.presentation_service import PresentationService
from apps.accounting.services.business_line_service import BusinessLineService
from apps.accounting.services.revenue_calculation_utils import RevenueCalculationMixin
from apps.core.mixins import (
    BusinessLinePermissionMixin,
    BusinessLineHierarchyMixin
)
from apps.core.constants import SERVICE_CATEGORIES


class BusinessLineDetailView(
    LoginRequiredMixin, 
    BusinessLinePermissionMixin, 
    BusinessLineHierarchyMixin,
    DetailView
):
    model = BusinessLine
    template_name = 'accounting/business_line_detail.html'
    context_object_name = 'business_line'
    
    def get_object(self):
        line_path = self.kwargs.get('line_path', '')
        business_line = self.resolve_business_line_from_path(line_path)
        self.check_business_line_permission(business_line)
        return business_line
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template_service = TemplateDataService()
        detail_context = template_service.prepare_business_line_detail_context(self.object)
        presentation_service = PresentationService()
        presentation_data = presentation_service.prepare_business_line_presentation(
            self.object, 
            self.request.user
        )
        context.update(detail_context)
        context['presentation'] = presentation_data
        return context


class BusinessLineListView(
    LoginRequiredMixin,
    BusinessLinePermissionMixin,
    ListView
):
    model = BusinessLine
    template_name = 'accounting/business_line_list.html'
    context_object_name = 'business_lines'
    paginate_by = 20
    
    def get_queryset(self):
        base_queryset = BusinessLine.objects.select_related('parent').all()
        filtered_queryset = self.filter_business_lines_by_permission(base_queryset)
        search_query = self.request.GET.get('search', '')
        if search_query:
            filtered_queryset = filtered_queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        return filtered_queryset.order_by('-is_active', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template_service = TemplateDataService()
        search_query = self.request.GET.get('search', '')
        list_context = template_service.prepare_business_line_list_context(
            business_lines=self.get_queryset(),
            search_query=search_query
        )
        context.update(list_context)
        return context


class BusinessLineHierarchyView(
    BusinessLineHierarchyMixin,
    PermissionRequiredMixin,
    TemplateView
):
    permission_required = 'accounting.view_businessline'
    template_name = 'accounting/hierarchy_navigation.html'
    
    def get_template_names(self):
        line_path = self.kwargs.get('line_path')
        if line_path:
            return ['accounting/business_line_detail.html']
        return ['accounting/hierarchy_navigation.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        line_path = kwargs.get('line_path')
        if line_path:
            hierarchy_context = self.get_business_line_context(line_path)
            context.update(hierarchy_context)
            current_line = hierarchy_context.get('business_line')
            if current_line:
                business_line_service = BusinessLineService()
                children = BusinessLine.objects.filter(parent=current_line)
                accessible_children = business_line_service.get_accessible_lines(self.request.user).filter(
                    parent=current_line
                )
                if not accessible_children.exists():
                    descendant_ids = current_line.get_descendant_ids()
                    services = ClientService.objects.filter(business_line__id__in=descendant_ids)
                    black_services = services.filter(category='black')
                    white_services = services.filter(category='white')
                    black_count = black_services.count()
                    white_count = white_services.count()
                    black_revenue = ServicePayment.objects.filter(
                        client_service__in=black_services
                    ).aggregate(total=RevenueCalculationMixin.get_net_revenue_aggregation())['total'] or 0
                    white_revenue = ServicePayment.objects.filter(
                        client_service__in=white_services
                    ).aggregate(total=RevenueCalculationMixin.get_net_revenue_aggregation())['total'] or 0
                    category_items = []
                    category_items.append({
                        'name': 'BLACK',
                        'category': 'BLACK',
                        'slug': 'black',
                        'type': 'category',
                        'count': black_count,
                        'total_revenue': black_revenue,
                        'total_services': black_count,
                        'url': f'/accounting/business-lines/{line_path}/black/',
                        'description': f'{black_count} servicios BLACK'
                    })
                    category_items.append({
                        'name': 'WHITE', 
                        'category': 'WHITE',
                        'slug': 'white',
                        'type': 'category',
                        'count': white_count,
                        'total_revenue': white_revenue,
                        'total_services': white_count,
                        'url': f'/accounting/business-lines/{line_path}/white/',
                        'description': f'{white_count} servicios WHITE'
                    })
                    context.update({
                        'current_line': current_line,
                        'items': category_items,
                        'show_categories': True,
                        'page_title': f'Categorías - {current_line.name}',
                        'page_subtitle': f'Categorías de servicios en {current_line.name}',
                        'subtitle': f'Categorías de servicios en {current_line.name}',
                        'show_hierarchy': True,
                        'view_type': 'categories',
                        'level_stats': {
                            'total_services': black_count + white_count,
                            'total_revenue': black_revenue + white_revenue,
                            'black_services': black_count,
                            'white_services': white_count,
                            'black_revenue': black_revenue,
                            'white_revenue': white_revenue,
                        }
                    })
                else:
                    descendant_ids = current_line.get_descendant_ids()
                    
                    payments = ServicePayment.objects.filter(
                        client_service__business_line__id__in=descendant_ids
                    )
                    
                    white_revenue = payments.filter(
                        client_service__category='white'
                    ).aggregate(total=RevenueCalculationMixin.get_net_revenue_aggregation())['total'] or 0
                    
                    black_revenue = payments.filter(
                        client_service__category='black'
                    ).aggregate(total=RevenueCalculationMixin.get_net_revenue_aggregation())['total'] or 0
                    
                    white_services = ClientService.objects.filter(
                        business_line__id__in=descendant_ids, category='white'
                    ).count()
                    
                    black_services = ClientService.objects.filter(
                        business_line__id__in=descendant_ids, category='black'
                    ).count()
                    
                    for child in accessible_children:
                        child_descendant_ids = child.get_descendant_ids()
                        child_payments = ServicePayment.objects.filter(
                            client_service__business_line__id__in=child_descendant_ids
                        )
                        child.white_revenue = child_payments.filter(
                            client_service__category='white'
                        ).aggregate(total=RevenueCalculationMixin.get_net_revenue_aggregation())['total'] or 0
                        child.black_revenue = child_payments.filter(
                            client_service__category='black'
                        ).aggregate(total=RevenueCalculationMixin.get_net_revenue_aggregation())['total'] or 0
                        child.white_services = ClientService.objects.filter(
                            business_line__id__in=child_descendant_ids, category='white'
                        ).count()
                        child.black_services = ClientService.objects.filter(
                            business_line__id__in=child_descendant_ids, category='black'
                        ).count()
                    
                    context.update({
                        'current_line': current_line,
                        'children': accessible_children,
                        'items': accessible_children,
                        'business_lines': accessible_children,
                        'page_title': f'Líneas de negocio - {current_line.name}',
                        'page_subtitle': f'Sublíneas de {current_line.name}',
                        'subtitle': f'Sublíneas de {current_line.name}',
                        'show_hierarchy': True,
                        'view_type': 'business_lines',
                        'level_stats': {
                            'white_revenue': white_revenue,
                            'black_revenue': black_revenue,
                            'white_services': white_services,
                            'black_services': black_services,
                            'children_count': accessible_children.count(),
                        }
                    })
        else:
            business_line_service = BusinessLineService()
            accessible_lines = business_line_service.get_accessible_lines(self.request.user)
            root_lines = business_line_service.get_root_lines_for_user(self.request.user)
            
            payments = ServicePayment.objects.filter(
                client_service__business_line__in=accessible_lines
            )
            white_revenue = payments.filter(
                client_service__category='white'
            ).aggregate(total=RevenueCalculationMixin.get_net_revenue_aggregation())['total'] or 0
            black_revenue = payments.filter(
                client_service__category='black'
            ).aggregate(total=RevenueCalculationMixin.get_net_revenue_aggregation())['total'] or 0
            
            total_lines = accessible_lines.count()
            
            for line in root_lines:
                line_descendant_ids = line.get_descendant_ids()
                line_payments = ServicePayment.objects.filter(
                    client_service__business_line__id__in=line_descendant_ids
                )
                line.white_revenue = line_payments.filter(
                    client_service__category='white'
                ).aggregate(total=RevenueCalculationMixin.get_net_revenue_aggregation())['total'] or 0
                line.black_revenue = line_payments.filter(
                    client_service__category='black'
                ).aggregate(total=RevenueCalculationMixin.get_net_revenue_aggregation())['total'] or 0
                line.white_services = ClientService.objects.filter(
                    business_line__id__in=line_descendant_ids, category='white'
                ).count()
                line.black_services = ClientService.objects.filter(
                    business_line__id__in=line_descendant_ids, category='black'
                ).count()
            
            context.update({
                'business_lines': root_lines,
                'items': root_lines,
                'accessible_lines': accessible_lines,
                'page_title': 'Gestión por Líneas de Negocio',
                'page_subtitle': 'Administra y visualiza tus líneas de negocio',
                'subtitle': 'Administra y visualiza tus líneas de negocio',
                'show_hierarchy': True,
                'view_type': 'business_lines',
                'level_stats': {
                    'total_lines': total_lines,
                    'white_revenue': white_revenue,
                    'black_revenue': black_revenue,
                }
            })
        return context


class BusinessLineCreateView(LoginRequiredMixin, CreateView):
    model = BusinessLine
    template_name = 'business_lines/business_line_form.html'
    fields = ['name', 'parent']
    
    def dispatch(self, request, *args, **kwargs):
        if getattr(request.user, 'role', None) != 'ADMIN':
            raise PermissionDenied(
                "Solo los administradores pueden gestionar líneas de negocio."
            )
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        initial = super().get_initial()
        parent_id = self.kwargs.get('parent')
        if parent_id:
            try:
                parent = BusinessLine.objects.get(pk=parent_id)
                initial['parent'] = parent
            except BusinessLine.DoesNotExist:
                pass
        return initial
    
    def get_success_url(self):
        return reverse('accounting:business-lines')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Línea de negocio "{self.object.name}" creada exitosamente.'
        )
        return response


def get_business_line_path_hierarchy(business_line):
    hierarchy = []
    current = business_line
    while current:
        hierarchy.insert(0, current)
        current = current.parent
    return hierarchy


def build_business_line_breadcrumbs(business_line, view_name='accounting:business_line_detail'):
    from apps.accounting.services.navigation_service import HierarchicalNavigationService
    navigation_service = HierarchicalNavigationService()
    return navigation_service.build_breadcrumb_path(
        business_line=business_line,
        include_base=False
    )


def calculate_business_line_metrics(business_line):
    from apps.accounting.services.template_service import TemplateDataService
    template_service = TemplateDataService()
    return template_service.business_line_service.calculate_business_line_metrics(business_line)
