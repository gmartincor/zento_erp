from django.db.models import Q, Sum, Count, Avg
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError

from apps.business_lines.models import BusinessLine
from apps.accounting.models import ClientService, ServicePayment
from .revenue_calculation_utils import RevenueCalculationMixin

User = get_user_model()


class BusinessLineService(RevenueCalculationMixin):
    def get_accessible_lines(self, user):
        return BusinessLine.objects.select_related('parent').all()
    
    def get_root_lines_for_user(self, user):
        return self.get_accessible_lines(user).filter(level=1)
    
    def resolve_line_from_path(self, line_path):
        if not line_path or not line_path.strip():
            raise ValidationError("Empty line path provided")
        
        path_parts = line_path.strip('/').split('/')
        
        if len(path_parts) == 1:
            return BusinessLine.objects.select_related('parent').get(
                slug=path_parts[0], 
                level=1
            )
        
        current_line = None
        for i, slug in enumerate(path_parts):
            if i == 0:
                current_line = BusinessLine.objects.select_related('parent').get(
                    slug=slug, 
                    level=1
                )
            else:
                current_line = BusinessLine.objects.select_related('parent').get(
                    slug=slug,
                    parent=current_line,
                    level=i + 1
                )
        
        return current_line
    
    def build_line_path(self, business_line):
        if not business_line:
            return ''
        
        path_parts = []
        current = business_line
        
        while current:
            path_parts.insert(0, current.slug)
            current = current.parent
        
        return '/'.join(path_parts)
    
    def check_user_permission(self, user, business_line):
        return True
    
    def enforce_permission(self, user, business_line):
        pass
    
    def get_children_for_display(self, business_line, user_permissions=None):
        children = business_line.children.select_related('parent').filter(is_active=True)
        
        if user_permissions is not None:
            children = children.filter(id__in=user_permissions.values_list('id', flat=True))
        
        children = children.annotate(
            white_service_count=Count(
                'client_services',
                filter=Q(client_services__category='WHITE', client_services__is_active=True)
            ),
            black_service_count=Count(
                'client_services',
                filter=Q(client_services__category='BLACK', client_services__is_active=True)
            )
        )
        
        return children.order_by('name')
    
    def get_hierarchical_view(self, accessible_lines):
        return accessible_lines.select_related('parent').order_by('level', 'name')
    
    def get_business_line_stats(self, business_line, include_children=False):
        services_query = ClientService.objects.filter(
            business_line=business_line
        )
        
        if include_children:
            descendant_ids = business_line.get_descendant_ids()
            services_query = ClientService.objects.filter(
                business_line__id__in=descendant_ids
            )
        
        payments_query = ServicePayment.objects.filter(
            client_service__in=services_query
        )
        
        stats = payments_query.aggregate(
            total_revenue=self.get_net_revenue_aggregation(),
            avg_price=self.get_avg_net_revenue_aggregation(),
        )
        
        service_stats = services_query.aggregate(
            total_services=Count('id'),
            white_count=Count('id', filter=Q(category='WHITE')),
            black_count=Count('id', filter=Q(category='BLACK')),
        )
        
        payment_category_stats = payments_query.aggregate(
            white_revenue=self.get_net_revenue_with_filter(Q(client_service__category='WHITE')),
            black_revenue=self.get_net_revenue_with_filter(Q(client_service__category='BLACK')),
        )
        
        stats.update(service_stats)
        stats.update(payment_category_stats)
        
        stats['total_revenue'] = stats['total_revenue'] or 0
        stats['total_services'] = stats['total_services'] or 0
        stats['avg_price'] = stats['avg_price'] or 0
        stats['white_count'] = stats['white_count'] or 0
        stats['black_count'] = stats['black_count'] or 0
        stats['white_revenue'] = stats['white_revenue'] or 0
        stats['black_revenue'] = stats['black_revenue'] or 0
        
        if stats['total_revenue'] > 0:
            stats['white_percentage'] = (stats['white_revenue'] / stats['total_revenue']) * 100
            stats['black_percentage'] = (stats['black_revenue'] / stats['total_revenue']) * 100
        else:
            stats['white_percentage'] = 0
            stats['black_percentage'] = 0
        
        return stats
