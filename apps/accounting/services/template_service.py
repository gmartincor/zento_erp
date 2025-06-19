"""
Template Service - Centralizes template data preparation.

This service consolidates data preparation logic that was previously
scattered across templates, improving maintainability and testability.
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional
from collections import defaultdict

from django.db.models import QuerySet, Sum, Count, Avg
from django.utils import timezone

from apps.business_lines.models import BusinessLine
from apps.accounting.models import ClientService
from apps.core.constants import SERVICE_CATEGORIES


class CategoryStatsService:
    """Service for calculating category-based statistics."""
    
    def calculate_category_summary(self, services: QuerySet) -> Dict[str, Any]:
        """
        Calculate summary statistics for service categories.
        
        Args:
            services: QuerySet of ClientService objects
            
        Returns:
            Dictionary with category summary data
        """
        category_data = services.values('category').annotate(
            total_amount=Sum('price'),
            service_count=Count('id')
        ).order_by('-total_amount')
        
        total_amount = sum(item['total_amount'] or 0 for item in category_data)
        total_categories = len(category_data)
        
        # Calculate breakdown with percentages
        category_breakdown = []
        for item in category_data:
            amount = item['total_amount'] or 0
            percentage = (amount / total_amount * 100) if total_amount > 0 else 0
            average = amount / item['service_count'] if item['service_count'] > 0 else 0
            
            category_breakdown.append({
                'category_name': dict(SERVICE_CATEGORIES).get(
                    item['category'], 
                    item['category'] or 'Sin categoría'
                ),
                'category_code': item['category'],
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
        """
        Calculate category statistics for business line list view.
        
        Args:
            business_lines: QuerySet of BusinessLine objects
            
        Returns:
            Dictionary with category statistics by type
        """
        all_services = ClientService.objects.filter(
            business_line__in=business_lines,
            is_active=True
        )
        
        stats_by_category = {}
        
        for category_code, category_name in SERVICE_CATEGORIES.items():
            category_services = all_services.filter(category=category_code)
            category_stats = category_services.aggregate(
                total_revenue=Sum('price'),
                total_services=Count('id')
            )
            
            stats_by_category[category_code] = {
                'name': category_name,
                'total_revenue': category_stats['total_revenue'] or 0,
                'total_services': category_stats['total_services'] or 0
            }
        
        return stats_by_category


class ClientStatsService:
    """Service for calculating client-based statistics."""
    
    def calculate_client_summary(self, services: QuerySet) -> Dict[str, Any]:
        """
        Calculate summary statistics for clients.
        
        Args:
            services: QuerySet of ClientService objects
            
        Returns:
            Dictionary with client summary data
        """
        client_data = services.values(
            'client__id',
            'client__name',
            'client__email'
        ).annotate(
            total_amount=Sum('price'),
            service_count=Count('id')
        ).order_by('-total_amount')
        
        total_amount = sum(item['total_amount'] or 0 for item in client_data)
        total_clients = len(client_data)
        
        # Calculate breakdown with percentages
        client_breakdown = []
        for item in client_data:
            amount = item['total_amount'] or 0
            percentage = (amount / total_amount * 100) if total_amount > 0 else 0
            average = amount / item['service_count'] if item['service_count'] > 0 else 0
            
            client_breakdown.append({
                'client_id': item['client__id'],
                'client_name': item['client__name'],
                'client_email': item['client__email'],
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
    """Service for calculating business line statistics."""
    
    def calculate_global_stats(self, business_lines: QuerySet) -> Dict[str, Any]:
        """
        Calculate global statistics across all business lines.
        
        Args:
            business_lines: QuerySet of BusinessLine objects
            
        Returns:
            Dictionary with global statistics
        """
        all_services = ClientService.objects.filter(
            business_line__in=business_lines,
            is_active=True
        )
        
        global_stats = all_services.aggregate(
            total_revenue=Sum('price'),
            total_services=Count('id')
        )
        
        return {
            'total_revenue': global_stats['total_revenue'] or 0,
            'total_services': global_stats['total_services'] or 0,
            'total_lines': business_lines.count()
        }
    
    def calculate_business_line_metrics(self, business_line: BusinessLine) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for a single business line.
        
        Args:
            business_line: BusinessLine instance
            
        Returns:
            Dictionary with business line metrics
        """
        # Get all descendants including self
        descendant_lines = business_line.get_descendants(include_self=True)
        services = ClientService.objects.filter(
            business_line__in=descendant_lines,
            is_active=True
        )
        
        # Basic metrics
        basic_stats = services.aggregate(
            total_revenue=Sum('price'),
            total_services=Count('id'),
            avg_service_value=Avg('price')
        )
        
        # Category distribution
        category_stats = CategoryStatsService().calculate_category_summary(services)
        
        # Client metrics
        client_stats = ClientStatsService().calculate_client_summary(services)
        
        # Time-based metrics (last 30 days)
        recent_cutoff = timezone.now() - timezone.timedelta(days=30)
        recent_services = services.filter(created_at__gte=recent_cutoff)
        recent_stats = recent_services.aggregate(
            recent_revenue=Sum('price'),
            recent_services=Count('id')
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
    """Service for handling hierarchical navigation data."""
    
    def build_navigation_context(self, business_line: BusinessLine) -> Dict[str, Any]:
        """
        Build navigation context for a business line.
        
        Args:
            business_line: BusinessLine instance
            
        Returns:
            Dictionary with navigation context
        """
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
        """Get the full hierarchy path from root to current business line."""
        path = []
        current = business_line
        
        while current:
            path.insert(0, current)
            current = current.parent
        
        return path
    
    def _build_breadcrumbs(self, hierarchy: List[BusinessLine]) -> List[Dict[str, Any]]:
        """Build breadcrumb navigation from hierarchy path."""
        breadcrumbs = []
        
        for i, line in enumerate(hierarchy):
            # Build URL path
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
    """Main service for consolidating template data preparation."""
    
    def __init__(self):
        self.category_service = CategoryStatsService()
        self.client_service = ClientStatsService()
        self.business_line_service = BusinessLineStatsService()
        self.navigation_service = HierarchyNavigationService()
    
    def prepare_business_line_list_context(self, business_lines: QuerySet, search_query: str = '') -> Dict[str, Any]:
        """
        Prepare context data for business line list view.
        
        Args:
            business_lines: QuerySet of BusinessLine objects
            search_query: Optional search query string
            
        Returns:
            Dictionary with complete context data
        """
        # Global statistics
        global_stats = self.business_line_service.calculate_global_stats(business_lines)
        
        # Category statistics
        category_stats = self.category_service.calculate_category_stats_for_list(business_lines)
        
        return {
            'global_stats': global_stats,
            'category_stats': category_stats,
            'total_lines_count': business_lines.count(),
            'search_query': search_query,
            'has_search': bool(search_query)
        }
    
    def prepare_business_line_detail_context(self, business_line: BusinessLine) -> Dict[str, Any]:
        """
        Prepare context data for business line detail view.
        
        Args:
            business_line: BusinessLine instance
            
        Returns:
            Dictionary with complete context data
        """
        # Navigation context
        navigation_context = self.navigation_service.build_navigation_context(business_line)
        
        # Business line metrics
        metrics = self.business_line_service.calculate_business_line_metrics(business_line)
        
        # Combine all context
        context = {
            **navigation_context,
            **metrics,
            'page_title': business_line.name,
            'page_subtitle': business_line.description or f'Gestión de {business_line.name}'
        }
        
        return context
    
    def prepare_category_summary_context(self, services: QuerySet) -> Dict[str, Any]:
        """
        Prepare context data for category summary view.
        
        Args:
            services: QuerySet of ClientService objects
            
        Returns:
            Dictionary with complete context data
        """
        category_summary = self.category_service.calculate_category_summary(services)
        
        return {
            'category_summary': category_summary,
            'category_breakdown': category_summary['category_breakdown']
        }
    
    def prepare_client_revenue_context(self, services: QuerySet) -> Dict[str, Any]:
        """
        Prepare context data for client revenue view.
        
        Args:
            services: QuerySet of ClientService objects
            
        Returns:
            Dictionary with complete context data
        """
        client_summary = self.client_service.calculate_client_summary(services)
        
        return {
            'client_summary': client_summary,
            'client_breakdown': client_summary['client_breakdown']
        }
