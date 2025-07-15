from django.db.models import QuerySet, Q, Sum, Count, Avg
from apps.accounting.models import ServicePayment, ClientService
from apps.core.constants import SERVICE_CATEGORIES
from .revenue_calculation_utils import RevenueCalculationMixin


class HistoryService(RevenueCalculationMixin):
    
    @staticmethod
    def _apply_common_filters(queryset: QuerySet, filters: dict, is_payment_query: bool = False) -> QuerySet:
        if not filters:
            return queryset
            
        if filters.get('search'):
            if is_payment_query:
                search_fields = [
                    'client_service__client__full_name__icontains',
                    'client_service__business_line__name__icontains'
                ]
            else:
                search_fields = [
                    'client__full_name__icontains',
                    'business_line__name__icontains'
                ]
            
            search_q = Q()
            for field in search_fields:
                search_q |= Q(**{field: filters['search']})
            queryset = queryset.filter(search_q)
            
        if filters.get('category'):
            category_field = 'client_service__category' if is_payment_query else 'category'
            queryset = queryset.filter(**{category_field: filters['category']})
            
        return queryset
    
    @classmethod
    def get_client_services_history(cls, client_id: int, filters: dict = None) -> QuerySet:
        queryset = ClientService.objects.filter(
            client_id=client_id
        ).select_related(
            'client', 'business_line', 'business_line__parent'
        ).prefetch_related('payments').order_by('-created')
        
        if filters and filters.get('is_active') is not None:
            is_active = filters['is_active'].lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
            
        return cls._apply_common_filters(queryset, filters)
    
    @classmethod
    def get_global_payments_history(cls, filters: dict = None) -> QuerySet:
        queryset = ServicePayment.objects.filter(
            status=ServicePayment.StatusChoices.PAID
        ).select_related(
            'client_service__client',
            'client_service__business_line'
        ).order_by('-payment_date')
        
        queryset = cls._apply_common_filters(queryset, filters, is_payment_query=True)
        
        if filters and filters.get('service_id'):
            queryset = queryset.filter(client_service_id=filters['service_id'])
                
        return queryset
    
    @staticmethod
    def get_service_payment_history(service_id: int) -> QuerySet:
        return ServicePayment.objects.filter(
            client_service_id=service_id
        ).order_by('-payment_date')
    
    @classmethod
    def get_history_summary(cls, client_id: int = None, service_id: int = None) -> dict:
        from decimal import Decimal
        summary = {}
        
        if client_id:
            services = cls.get_client_services_history(client_id)
            
            summary.update({
                'total_services': services.count(),
                'active_services': services.filter(is_active=True).count(),
            })
            
            service_stats = services.aggregate(
                white_services=Count('id', filter=Q(category=SERVICE_CATEGORIES['PERSONAL'])),
                black_services=Count('id', filter=Q(category=SERVICE_CATEGORIES['BUSINESS']))
            )
            summary.update(service_stats)
            
            from apps.accounting.models import ServicePayment
            payment_stats = ServicePayment.objects.filter(
                client_service__in=services,
                status=ServicePayment.StatusChoices.PAID
            ).aggregate(
                total_revenue=RevenueCalculationMixin.get_net_revenue_aggregation(),
                white_revenue=RevenueCalculationMixin.get_net_revenue_with_filter(Q(client_service__category=SERVICE_CATEGORIES['PERSONAL'])),
                black_revenue=RevenueCalculationMixin.get_net_revenue_with_filter(Q(client_service__category=SERVICE_CATEGORIES['BUSINESS']))
            )
            
            summary.update({
                'total_revenue': payment_stats['total_revenue'] or Decimal('0'),
                'white_services': service_stats['white_services'] or 0,
                'black_services': service_stats['black_services'] or 0,
                'white_revenue': payment_stats['white_revenue'] or Decimal('0'),
                'black_revenue': payment_stats['black_revenue'] or Decimal('0'),
            })
        
        if service_id:
            payments = cls.get_service_payment_history(service_id)
            summary.update({
                'total_payments': payments.count(),
                'total_paid': payments.aggregate(
                    total=RevenueCalculationMixin.get_net_revenue_aggregation()
                )['total'] or Decimal('0'),
                'average_payment': payments.aggregate(
                    avg=RevenueCalculationMixin.get_avg_net_revenue_aggregation()
                )['avg'] or Decimal('0'),
            })
            
        return summary
