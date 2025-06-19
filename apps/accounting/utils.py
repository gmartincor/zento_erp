"""
Utilities for the accounting module - Refactored.

This module provides utility classes that serve as adapters between
the old interface and new service-based architecture. Maintains backward
compatibility while delegating to proper service layer.
"""

from apps.business_lines.models import BusinessLine
from apps.accounting.services.business_line_service import BusinessLineService
from apps.accounting.services.statistics_service import StatisticsService


class BusinessLineNavigator:
    """
    Utility class for navigating business line hierarchies.
    
    DEPRECATED: Use BusinessLineService directly for new code.
    This class maintains backward compatibility with existing views.
    """
    
    def __init__(self):
        self.service = BusinessLineService()
    
    @staticmethod
    def get_business_line_by_path(line_path):
        """
        Get a business line by its hierarchical path.
        
        Args:
            line_path (str): Path like 'jaen/pepe/pepe-normal'
            
        Returns:
            BusinessLine: The resolved business line object
            
        Raises:
            BusinessLine.DoesNotExist: If path doesn't resolve to valid business line
        """
        service = BusinessLineService()
        return service.resolve_line_from_path(line_path)
    
    @staticmethod
    def build_line_path(business_line):
        """
        Build hierarchical path string for a business line.
        
        Args:
            business_line (BusinessLine): Business line object
            
        Returns:
            str: Path string like 'jaen/pepe/pepe-normal'
        """
        service = BusinessLineService()
        return service.build_line_path(business_line)
    
    @staticmethod
    def get_children_for_display(business_line, user_permissions=None):
        """
        Get child business lines suitable for navigation display.
        
        Args:
            business_line (BusinessLine): Parent business line
            user_permissions (QuerySet, optional): User's allowed business lines
            
        Returns:
            QuerySet: Child business lines with service counts
        """
        service = BusinessLineService()
        return service.get_children_for_display(business_line, user_permissions)
    
    @staticmethod
    def get_root_lines_for_user(user):
        """
        Get root-level business lines accessible to a user.
        
        Args:
            user: User object with role and business_lines relationship
            
        Returns:
            QuerySet: Root business lines
        """
        service = BusinessLineService()
        return service.get_root_lines_for_user(user)
    
    @staticmethod
    def get_hierarchical_view(accessible_lines):
        """
        Get business lines organized for hierarchical display.
        
        Args:
            accessible_lines: User's accessible business lines
            
        Returns:
            QuerySet ordered for hierarchy display
        """
        service = BusinessLineService()
        return service.get_hierarchical_view(accessible_lines)


class ServiceStatisticsCalculator:
    """
    Utility class for calculating service statistics.
    
    DEPRECATED: Use StatisticsService directly for new code.
    This class maintains backward compatibility with existing views.
    """
    
    def __init__(self):
        self.service = StatisticsService()
    
    @staticmethod
    def calculate_business_line_stats(business_line, include_children=True):
        """
        Calculate comprehensive statistics for a business line.
        
        Args:
            business_line (BusinessLine): Business line to analyze
            include_children (bool): Whether to include children statistics
            
        Returns:
            dict: Statistics dictionary
        """
        service = StatisticsService()
        return service.calculate_business_line_stats(business_line, include_children)
    
    @staticmethod
    def get_revenue_summary_by_period(business_lines, year=None, month=None):
        """
        Get revenue summary for business lines filtered by time period.
        
        Args:
            business_lines: Business lines to analyze
            year: Optional year filter
            month: Optional month filter
            
        Returns:
            dict: Revenue summary
        """
        service = StatisticsService()
        return service.get_revenue_summary_by_period(business_lines, year, month)
    
    @staticmethod
    def calculate_category_performance(category, business_lines):
        """
        Calculate performance metrics for a specific category.
        
        Args:
            category: Category to analyze ('WHITE' or 'BLACK')
            business_lines: QuerySet of business lines
            
        Returns:
            dict: Category-specific metrics
        """
        service = StatisticsService()
        return service.calculate_category_performance(category, business_lines)
    
    @staticmethod
    def get_client_performance_analysis(business_lines, limit=10):
        """
        Analyze client performance across business lines.
        
        Args:
            business_lines: QuerySet of business lines
            limit: Number of top clients to return
            
        Returns:
            dict: Client analysis
        """
        service = StatisticsService()
        return service.get_client_performance_analysis(business_lines, limit)


# Legacy function wrappers for backward compatibility
def get_business_line_by_path(line_path):
    """Legacy function - use BusinessLineService instead."""
    return BusinessLineNavigator.get_business_line_by_path(line_path)


def calculate_business_line_stats(business_line, include_children=True):
    """Legacy function - use StatisticsService instead."""
    return ServiceStatisticsCalculator.calculate_business_line_stats(
        business_line, include_children
    )
