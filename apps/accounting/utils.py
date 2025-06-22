from apps.business_lines.models import BusinessLine
from apps.accounting.services.business_line_service import BusinessLineService
from apps.accounting.services.statistics_service import StatisticsService


class BusinessLineNavigator:
    def __init__(self):
        self.service = BusinessLineService()
    
    @staticmethod
    def get_business_line_by_path(line_path):
        service = BusinessLineService()
        return service.resolve_line_from_path(line_path)
    
    @staticmethod
    def build_line_path(business_line):
        service = BusinessLineService()
        return service.build_line_path(business_line)
    
    @staticmethod
    def get_children_for_display(business_line, user_permissions=None):
        service = BusinessLineService()
        return service.get_children_for_display(business_line, user_permissions)
    
    @staticmethod
    def get_root_lines_for_user(user):
        service = BusinessLineService()
        return service.get_root_lines_for_user(user)
    
    @staticmethod
    def get_hierarchical_view(accessible_lines):
        service = BusinessLineService()
        return service.get_hierarchical_view(accessible_lines)


class ServiceStatisticsCalculator:
    def __init__(self):
        self.service = StatisticsService()
    
    @staticmethod
    def calculate_business_line_stats(business_line, include_children=True):
        service = StatisticsService()
        return service.calculate_business_line_stats(business_line, include_children)
    
    @staticmethod
    def get_revenue_summary_by_period(business_lines, year=None, month=None):
        service = StatisticsService()
        return service.get_revenue_summary_by_period(business_lines, year, month)
    
    @staticmethod
    def calculate_category_performance(category, business_lines):
        service = StatisticsService()
        return service.calculate_category_performance(category, business_lines)
    
    @staticmethod
    def get_client_performance_analysis(business_lines, limit=10):
        service = StatisticsService()
        return service.get_client_performance_analysis(business_lines, limit)


def get_business_line_by_path(line_path):
    return BusinessLineNavigator.get_business_line_by_path(line_path)


def calculate_business_line_stats(business_line, include_children=True):
    return ServiceStatisticsCalculator.calculate_business_line_stats(
        business_line, include_children
    )
