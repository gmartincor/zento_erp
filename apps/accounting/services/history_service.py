from django.db.models import QuerySet, Q, Sum, Count, Avg
from apps.accounting.models import ServicePayment, ClientService


class HistoryService:
    
    @staticmethod
    def get_client_services_history(client_id: int, filters: dict = None) -> QuerySet:
        queryset = ClientService.objects.filter(
            client_id=client_id
        ).select_related(
            'client', 'business_line', 'business_line__parent'
        ).prefetch_related('payments').order_by('-created')
        
        if filters:
            if filters.get('is_active') is not None:
                is_active = filters['is_active'].lower() == 'true'
                queryset = queryset.filter(is_active=is_active)
            if filters.get('category'):
                queryset = queryset.filter(category=filters['category'])
                
        return queryset
    
    @staticmethod
    def get_global_payments_history(filters: dict = None) -> QuerySet:
        queryset = ServicePayment.objects.filter(
            status=ServicePayment.StatusChoices.PAID
        ).select_related(
            'client_service__client',
            'client_service__business_line'
        ).order_by('-payment_date')
        
        if filters:
            if filters.get('business_line'):
                queryset = queryset.filter(
                    client_service__business_line__slug=filters['business_line']
                )
            if filters.get('category'):
                queryset = queryset.filter(
                    client_service__category=filters['category'].upper()
                )
            if filters.get('service_id'):
                queryset = queryset.filter(
                    client_service_id=filters['service_id']
                )
                
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
                white_services=Count('id', filter=Q(category='white')),
                black_services=Count('id', filter=Q(category='black'))
            )
            summary.update(service_stats)
            
            from apps.accounting.models import ServicePayment
            payment_stats = ServicePayment.objects.filter(
                client_service__in=services,
                status=ServicePayment.StatusChoices.PAID
            ).aggregate(
                total_revenue=Sum('amount'),
                white_revenue=Sum('amount', filter=Q(client_service__category='white')),
                black_revenue=Sum('amount', filter=Q(client_service__category='black'))
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
                    total=Sum('amount')
                )['total'] or Decimal('0'),
                'average_payment': payments.aggregate(
                    avg=Avg('amount')
                )['avg'] or Decimal('0'),
            })
            
        return summary
