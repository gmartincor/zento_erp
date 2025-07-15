from django.db.models import Count
from apps.accounting.models import ClientService, ServicePayment
from apps.accounting.services.revenue_calculation_utils import RevenueCalculationMixin
from apps.core.constants import SERVICE_CATEGORIES


class BusinessLineStatsCalculator(RevenueCalculationMixin):
    
    @classmethod
    def enrich_business_line_with_stats(cls, business_line):
        line_descendant_ids = business_line.get_descendant_ids()
        line_payments = ServicePayment.objects.filter(
            client_service__business_line__id__in=line_descendant_ids
        )
        
        business_line.personal_revenue = line_payments.filter(
            client_service__category=SERVICE_CATEGORIES['PERSONAL']
        ).aggregate(total=cls.get_net_revenue_aggregation())['total'] or 0
        
        business_line.business_revenue = line_payments.filter(
            client_service__category=SERVICE_CATEGORIES['BUSINESS']
        ).aggregate(total=cls.get_net_revenue_aggregation())['total'] or 0
        
        business_line.personal_services = ClientService.objects.filter(
            business_line__id__in=line_descendant_ids,
            category=SERVICE_CATEGORIES['PERSONAL']
        ).count()
        
        business_line.business_services = ClientService.objects.filter(
            business_line__id__in=line_descendant_ids,
            category=SERVICE_CATEGORIES['BUSINESS']
        ).count()
        
        return business_line
    
    @classmethod
    def enrich_business_lines_with_stats(cls, business_lines):
        for line in business_lines:
            cls.enrich_business_line_with_stats(line)
        return business_lines
