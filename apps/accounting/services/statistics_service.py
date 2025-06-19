"""
Statistics Service - Enhanced statistical calculations and reporting.

This service centralizes all statistical calculations for the accounting module,
providing comprehensive analytics following separation of concerns principles.
"""

from decimal import Decimal
from django.db.models import Q, Sum, Count, Avg, QuerySet
from django.utils import timezone
from datetime import datetime, timedelta

from apps.business_lines.models import BusinessLine
from apps.accounting.models import ClientService


class StatisticsService:
    """
    Service class for statistical calculations and analytics.
    
    Provides comprehensive statistical analysis with focus on:
    - Business line performance
    - Revenue analysis
    - Category comparisons
    - Client insights
    """
    
    def calculate_business_line_stats(self, business_line, include_children=True):
        """
        Calculate comprehensive statistics for a business line.
        
        Args:
            business_line: BusinessLine to analyze
            include_children: Whether to include child line statistics
            
        Returns:
            Dictionary with comprehensive statistics
        """
        # Get services queryset
        services_query = self._get_services_for_line(business_line, include_children)
        
        # Basic aggregations
        stats = services_query.aggregate(
            total_revenue=Sum('price'),
            total_services=Count('id'),
            white_services=Count('id', filter=Q(category='WHITE')),
            black_services=Count('id', filter=Q(category='BLACK')),
            white_revenue=Sum('price', filter=Q(category='WHITE')),
            black_revenue=Sum('price', filter=Q(category='BLACK')),
            unique_clients=Count('client', distinct=True),
            avg_price=Avg('price')
        )
        
        # Calculate remanente totals for BLACK services
        total_remanentes = self._calculate_remanente_totals(
            services_query.filter(category='BLACK')
        )
        
        # Normalize and calculate derived metrics
        return self._normalize_stats(stats, total_remanentes)
    
    def get_revenue_summary_by_period(self, business_lines, year=None, month=None):
        """
        Get revenue summary for business lines filtered by time period.
        
        Args:
            business_lines: QuerySet of business lines to analyze
            year: Optional year filter
            month: Optional month filter
            
        Returns:
            Dictionary with period-based revenue analysis
        """
        # Build base query
        services_query = ClientService.objects.filter(
            business_line__in=business_lines,
            is_active=True
        )
        
        # Apply date filters
        services_query = self._apply_date_filters(services_query, year, month)
        
        # Calculate statistics
        period_stats = services_query.aggregate(
            total_revenue=Sum('price'),
            total_services=Count('id'),
            white_revenue=Sum('price', filter=Q(category='WHITE')),
            black_revenue=Sum('price', filter=Q(category='BLACK')),
            unique_clients=Count('client', distinct=True)
        )
        
        # Add period context
        period_info = self._get_period_info(year, month)
        
        return {
            **self._normalize_basic_stats(period_stats),
            'period_info': period_info,
            'business_lines_count': business_lines.count()
        }
    
    def calculate_category_performance(self, category, business_lines):
        """
        Calculate performance metrics for a specific category.
        
        Args:
            category: Category to analyze ('WHITE' or 'BLACK')
            business_lines: QuerySet of business lines
            
        Returns:
            Dictionary with category-specific metrics
        """
        services_query = ClientService.objects.filter(
            business_line__in=business_lines,
            category=category,
            is_active=True
        )
        
        stats = services_query.aggregate(
            total_revenue=Sum('price'),
            service_count=Count('id'),
            avg_price=Avg('price'),
            unique_clients=Count('client', distinct=True)
        )
        
        # Add category-specific calculations
        if category == 'BLACK':
            stats['total_remanentes'] = self._calculate_remanente_totals(services_query)
        
        return self._normalize_basic_stats(stats)
    
    def get_client_performance_analysis(self, business_lines, limit=10):
        """
        Analyze client performance across business lines.
        
        Args:
            business_lines: QuerySet of business lines
            limit: Number of top clients to return
            
        Returns:
            Dictionary with client analysis
        """
        # Top clients by revenue
        top_clients = (
            ClientService.objects
            .filter(business_line__in=business_lines, is_active=True)
            .values('client__id', 'client__full_name', 'client__dni')
            .annotate(
                total_revenue=Sum('price'),
                service_count=Count('id'),
                avg_service_price=Avg('price')
            )
            .order_by('-total_revenue')[:limit]
        )
        
        # Client distribution statistics
        client_stats = self._calculate_client_distribution_stats(business_lines)
        
        return {
            'top_clients': list(top_clients),
            'client_stats': client_stats
        }
    
    def compare_periods(self, business_lines, current_year, current_month, 
                       previous_year=None, previous_month=None):
        """
        Compare performance between two periods.
        
        Args:
            business_lines: QuerySet of business lines
            current_year: Current period year
            current_month: Current period month
            previous_year: Previous period year (defaults to previous month)
            previous_month: Previous period month
            
        Returns:
            Dictionary with period comparison
        """
        # Current period stats
        current_stats = self.get_revenue_summary_by_period(
            business_lines, current_year, current_month
        )
        
        # Calculate previous period if not provided
        if previous_year is None or previous_month is None:
            prev_date = datetime(current_year, current_month, 1) - timedelta(days=1)
            previous_year = prev_date.year
            previous_month = prev_date.month
        
        # Previous period stats
        previous_stats = self.get_revenue_summary_by_period(
            business_lines, previous_year, previous_month
        )
        
        # Calculate changes
        revenue_change = self._calculate_percentage_change(
            previous_stats['total_revenue'],
            current_stats['total_revenue']
        )
        
        service_change = self._calculate_percentage_change(
            previous_stats['total_services'],
            current_stats['total_services']
        )
        
        return {
            'current_period': current_stats,
            'previous_period': previous_stats,
            'revenue_change': revenue_change,
            'service_change': service_change
        }
    
    # Private helper methods
    
    def _get_services_for_line(self, business_line, include_children):
        """Get services queryset for a business line with optional children."""
        if include_children:
            # Get all descendant business lines
            line_ids = [business_line.id]
            self._collect_descendant_ids(business_line, line_ids)
            return ClientService.objects.filter(
                business_line_id__in=line_ids,
                is_active=True
            )
        else:
            return ClientService.objects.filter(
                business_line=business_line,
                is_active=True
            )
    
    def _collect_descendant_ids(self, business_line, id_list):
        """Recursively collect descendant business line IDs."""
        for child in business_line.children.filter(is_active=True):
            id_list.append(child.id)
            self._collect_descendant_ids(child, id_list)
    
    def _calculate_remanente_totals(self, services_query):
        """Calculate total remanentes for BLACK category services."""
        total = Decimal('0')
        for service in services_query:
            total += Decimal(str(service.get_remanente_total()))
        return total
    
    def _normalize_stats(self, stats, total_remanentes):
        """Normalize statistics with safe defaults and calculated fields."""
        total_revenue = stats['total_revenue'] or Decimal('0')
        total_services = stats['total_services'] or 0
        
        return {
            'total_revenue': total_revenue,
            'total_services': total_services,
            'unique_clients': stats['unique_clients'] or 0,
            'white_services': stats['white_services'] or 0,
            'black_services': stats['black_services'] or 0,
            'white_revenue': stats['white_revenue'] or Decimal('0'),
            'black_revenue': stats['black_revenue'] or Decimal('0'),
            'avg_price': stats['avg_price'] or Decimal('0'),
            'total_remanentes': total_remanentes,
            'avg_revenue_per_service': total_revenue / max(total_services, 1)
        }
    
    def _normalize_basic_stats(self, stats):
        """Normalize basic statistics with safe defaults."""
        return {
            'total_revenue': stats.get('total_revenue') or Decimal('0'),
            'total_services': stats.get('total_services') or stats.get('service_count', 0),
            'white_revenue': stats.get('white_revenue') or Decimal('0'),
            'black_revenue': stats.get('black_revenue') or Decimal('0'),
            'unique_clients': stats.get('unique_clients') or 0,
            'avg_price': stats.get('avg_price') or Decimal('0'),
            'total_remanentes': stats.get('total_remanentes') or Decimal('0')
        }
    
    def _apply_date_filters(self, queryset, year, month):
        """Apply date filters to queryset."""
        if year:
            queryset = queryset.filter(start_date__year=year)
        if month:
            queryset = queryset.filter(start_date__month=month)
        return queryset
    
    def _get_period_info(self, year, month):
        """Get period information for context."""
        now = timezone.now()
        return {
            'year': year or now.year,
            'month': month or now.month,
            'is_current_month': (year == now.year and month == now.month) if year and month else False
        }
    
    def _calculate_client_distribution_stats(self, business_lines):
        """Calculate client distribution statistics."""
        stats = (
            ClientService.objects
            .filter(business_line__in=business_lines, is_active=True)
            .aggregate(
                total_clients=Count('client', distinct=True),
                total_services=Count('id'),
                avg_services_per_client=Avg('client__services__id')
            )
        )
        
        return self._normalize_basic_stats(stats)
    
    def _calculate_percentage_change(self, old_value, new_value):
        """Calculate percentage change between two values."""
        if not old_value or old_value == 0:
            return 100 if new_value else 0
        
        return ((new_value - old_value) / old_value) * 100
