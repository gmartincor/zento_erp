from decimal import Decimal
from typing import Dict, List, Any, Optional
from collections import defaultdict

from django.db.models import QuerySet, Sum, Count, Avg
from django.utils import timezone

from apps.business_lines.models import BusinessLine
from apps.accounting.models import ClientService, ServicePayment
from apps.accounting.services.navigation_service import HierarchicalNavigationService
from apps.core.constants import SERVICE_CATEGORIES


class CategoryStatsService:
    def calculate_category_summary(self, services: QuerySet) -> Dict[str, Any]:
        from apps.accounting.models import ServicePayment
        
        category_data = ServicePayment.objects.filter(
            client_service__in=services
        ).values('client_service__category').annotate(
            total_amount=Sum('amount'),
            service_count=Count('client_service__id', distinct=True)
        ).order_by('-total_amount')
        
        total_amount = sum(item['total_amount'] or 0 for item in category_data)
        total_categories = len(category_data)
        
        category_breakdown = []
        for item in category_data:
            amount = item['total_amount'] or 0
            percentage = (amount / total_amount * 100) if total_amount > 0 else 0
            average = amount / item['service_count'] if item['service_count'] > 0 else 0
            
            category_breakdown.append({
                'category_name': dict(SERVICE_CATEGORIES).get(
                    item['client_service__category'], 
                    item['client_service__category'] or 'Sin categoría'
                ),
                'category_code': item['client_service__category'],
                'total_amount': amount,
                'service_count': item['service_count'],
                'average_amount': average,
                'percentage': percentage
            })
        
        return {
            'total_categories': total_categories,
            'total_amount': total_amount,
            'average_per_category': total_amount / total_categories if total_categories > 0 else 0,
            'category_breakdown': category_breakdown
        }
    
    def calculate_category_stats_for_list(self, business_lines: QuerySet) -> Dict[str, Dict]:
        all_services = ClientService.objects.filter(
            business_line__in=business_lines,
            is_active=True
        )
        
        stats_by_category = {}
        
        for category_code, category_name in SERVICE_CATEGORIES.items():
            category_services = all_services.filter(category=category_code)
            category_stats = ServicePayment.objects.filter(
                client_service__in=category_services
            ).aggregate(
                total_revenue=Sum('amount'),
                total_services=Count('client_service__id', distinct=True)
            )
            
            stats_by_category[category_code] = {
                'name': category_name,
                'total_revenue': category_stats['total_revenue'] or 0,
                'total_services': category_stats['total_services'] or 0
            }
        
        return stats_by_category


class ClientStatsService:
    def calculate_client_summary(self, services: QuerySet) -> Dict[str, Any]:
        client_data = ServicePayment.objects.filter(
            client_service__in=services
        ).values(
            'client_service__client__id',
            'client_service__client__name',
            'client_service__client__email'
        ).annotate(
            total_amount=Sum('amount'),
            service_count=Count('client_service__id', distinct=True)
        ).order_by('-total_amount')
        
        total_amount = sum(item['total_amount'] or 0 for item in client_data)
        total_clients = len(client_data)
        
        client_breakdown = []
        for item in client_data:
            amount = item['total_amount'] or 0
            percentage = (amount / total_amount * 100) if total_amount > 0 else 0
            average = amount / item['service_count'] if item['service_count'] > 0 else 0
            
            client_breakdown.append({
                'client_id': item['client_service__client__id'],
                'client_name': item['client_service__client__name'],
                'client_email': item['client_service__client__email'],
                'total_amount': amount,
                'service_count': item['service_count'],
                'average_amount': average,
                'percentage': percentage
            })
        
        return {
            'total_clients': total_clients,
            'total_amount': total_amount,
            'average_per_client': total_amount / total_clients if total_clients > 0 else 0,
            'client_breakdown': client_breakdown
        }


class BusinessLineStatsService:
    def calculate_global_stats(self, business_lines: QuerySet) -> Dict[str, Any]:
        all_services = ClientService.objects.filter(
            business_line__in=business_lines,
            is_active=True
        )
        
        global_stats = ServicePayment.objects.filter(
            client_service__in=all_services
        ).aggregate(
            total_revenue=Sum('amount'),
            total_services=Count('client_service__id', distinct=True)
        )
        
        return {
            'total_revenue': global_stats['total_revenue'] or 0,
            'total_services': global_stats['total_services'] or 0,
            'total_lines': business_lines.count()
        }
    
    def calculate_business_line_metrics(self, business_line: BusinessLine) -> Dict[str, Any]:
        descendant_ids = business_line.get_descendant_ids()
        services = ClientService.objects.filter(
            business_line__id__in=descendant_ids,
            is_active=True
        )
        
        basic_stats = ServicePayment.objects.filter(
            client_service__in=services
        ).aggregate(
            total_revenue=Sum('amount'),
            total_services=Count('client_service__id', distinct=True),
            avg_service_value=Avg('amount')
        )
        
        category_stats = CategoryStatsService().calculate_category_summary(services)
        client_stats = ClientStatsService().calculate_client_summary(services)
        
        recent_cutoff = timezone.now() - timezone.timedelta(days=30)
        recent_services = services.filter(created__gte=recent_cutoff)
        recent_stats = ServicePayment.objects.filter(
            client_service__in=recent_services
        ).aggregate(
            recent_revenue=Sum('amount'),
            recent_services=Count('client_service__id', distinct=True)
        )
        
        return {
            'basic_metrics': {
                'total_revenue': basic_stats['total_revenue'] or 0,
                'total_services': basic_stats['total_services'] or 0,
                'average_service_value': basic_stats['avg_service_value'] or 0,
            },
            'category_metrics': category_stats,
            'client_metrics': client_stats,
            'recent_metrics': {
                'recent_revenue': recent_stats['recent_revenue'] or 0,
                'recent_services': recent_stats['recent_services'] or 0,
            },
            'hierarchy_info': {
                'has_children': business_line.children.exists(),
                'children_count': business_line.children.count(),
                'level': business_line.level,
                'is_leaf': not business_line.children.exists()
            }
        }


class HierarchyNavigationService:
    def build_navigation_context(self, business_line: BusinessLine) -> Dict[str, Any]:
        hierarchy = self._get_hierarchy_path(business_line)
        breadcrumbs = self._build_breadcrumbs(hierarchy)
        
        return {
            'hierarchy': hierarchy,
            'breadcrumbs': breadcrumbs,
            'parent': business_line.parent,
            'siblings': business_line.get_siblings() if business_line.parent else [],
            'children': list(business_line.children.filter(is_active=True)),
            'level': business_line.level,
            'is_root': business_line.level == 0,
            'is_leaf': not business_line.children.exists()
        }
    
    def _get_hierarchy_path(self, business_line: BusinessLine) -> List[BusinessLine]:
        path = []
        current = business_line
        
        while current:
            path.insert(0, current)
            current = current.parent
        
        return path
    
    def _build_breadcrumbs(self, hierarchy: List[BusinessLine]) -> List[Dict[str, Any]]:
        breadcrumbs = []
        
        for i, line in enumerate(hierarchy):
            path_segments = [ancestor.slug for ancestor in hierarchy[:i+1]]
            line_path = '/'.join(path_segments)
            
            breadcrumbs.append({
                'name': line.name,
                'url': f'/accounting/business-lines/{line_path}/',
                'is_current': i == len(hierarchy) - 1,
                'level': i
            })
        
        return breadcrumbs


class TemplateDataService:
    def __init__(self):
        self.category_service = CategoryStatsService()
        self.client_service = ClientStatsService()
        self.business_line_service = BusinessLineStatsService()
        self.navigation_service = HierarchicalNavigationService()
    
    def prepare_business_line_list_context(self, business_lines: QuerySet, search_query: str = '') -> Dict[str, Any]:
        global_stats = self.business_line_service.calculate_global_stats(business_lines)
        category_stats = self.category_service.calculate_category_stats_for_list(business_lines)
        
        return {
            'global_stats': global_stats,
            'category_stats': category_stats,
            'total_lines_count': business_lines.count(),
            'search_query': search_query,
            'has_search': bool(search_query)
        }
    
    def prepare_business_line_detail_context(self, business_line: BusinessLine) -> Dict[str, Any]:
        navigation_context = self.navigation_service.build_navigation_context(business_line)
        metrics = self.business_line_service.calculate_business_line_metrics(business_line)
        
        context = {
            **navigation_context,
            **metrics,
            'page_title': business_line.name,
            'page_subtitle': business_line.description or f'Gestión de {business_line.name}'
        }
        
        return context
    
    def prepare_category_summary_context(self, services: QuerySet) -> Dict[str, Any]:
        category_summary = self.category_service.calculate_category_summary(services)
        
        return {
            'category_summary': category_summary,
            'category_breakdown': category_summary['category_breakdown']
        }
    
    def prepare_client_revenue_context(self, services: QuerySet) -> Dict[str, Any]:
        client_summary = self.client_service.calculate_client_summary(services)
        
        return {
            'client_summary': client_summary,
            'client_breakdown': client_summary['client_breakdown']
        }
