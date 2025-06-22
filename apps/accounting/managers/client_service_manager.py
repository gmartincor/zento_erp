from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.db import models
from django.db.models import QuerySet, Q, Sum, Count, Avg, F
from django.contrib.auth import get_user_model

User = get_user_model()


class ClientServiceQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)
    
    def by_category(self, category: str):
        return self.filter(category=category)
    
    def by_business_line(self, business_line):
        return self.filter(business_line=business_line)
    
    def by_business_lines(self, business_lines: QuerySet):
        return self.filter(business_line__in=business_lines)
    
    def with_client_data(self):
        return self.select_related('client', 'business_line')
    
    def with_statistics(self):
        return self.annotate(
            client_name=F('client__full_name'),
            business_line_name=F('business_line__name')
        )


class ClientServiceManager(models.Manager):
    def get_queryset(self):
        return ClientServiceQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def by_category(self, category: str):
        return self.get_queryset().by_category(category)
    
    def get_services_by_category(
        self,
        business_line,
        category: str,
        active_only: bool = True
    ) -> QuerySet:
        queryset = self.get_queryset().by_business_line(business_line).by_category(category)
        if active_only:
            queryset = queryset.active()
        return queryset.with_client_data().order_by('-created')
    
    def get_services_by_category_including_descendants(
        self,
        business_line,
        category: str,
        active_only: bool = True
    ) -> QuerySet:
        descendant_ids = business_line.get_descendant_ids()
        
        queryset = self.get_queryset().filter(
            business_line__id__in=descendant_ids
        ).by_category(category)
        
        if active_only:
            queryset = queryset.active()
        
        return queryset.with_client_data().order_by('-created')
    
    def get_service_statistics(
        self,
        business_line,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        queryset = self.get_queryset().by_business_line(business_line).active()
        if category:
            queryset = queryset.by_category(category)
        stats = queryset.aggregate(
            total_services=Count('id'),
            total_revenue=Sum('price'),
            avg_price=Avg('price'),
            unique_clients=Count('client', distinct=True)
        )
        category_stats = {
            'WHITE': queryset.filter(category='WHITE').aggregate(
                count=Count('id'),
                revenue=Sum('price')
            ),
            'BLACK': queryset.filter(category='BLACK').aggregate(
                count=Count('id'),
                revenue=Sum('price')
            )
        }
        return {
            'total_services': stats['total_services'] or 0,
            'total_revenue': stats['total_revenue'] or Decimal('0'),
            'avg_price': stats['avg_price'] or Decimal('0'),
            'unique_clients': stats['unique_clients'] or 0,
            'category_breakdown': category_stats
        }
    
    def get_service_statistics_including_descendants(
        self,
        business_line,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        descendant_ids = business_line.get_descendant_ids()
        
        queryset = self.get_queryset().filter(
            business_line__id__in=descendant_ids
        ).active()
        
        if category:
            queryset = queryset.by_category(category)
            
        stats = queryset.aggregate(
            total_services=Count('id'),
            total_revenue=Sum('price'),
            avg_price=Avg('price'),
            unique_clients=Count('client', distinct=True)
        )
        
        category_stats = {
            'WHITE': queryset.filter(category='WHITE').aggregate(
                count=Count('id'),
                revenue=Sum('price')
            ),
            'BLACK': queryset.filter(category='BLACK').aggregate(
                count=Count('id'),
                revenue=Sum('price')
            )
        }
        
        return {
            'total_services': stats['total_services'] or 0,
            'total_revenue': stats['total_revenue'] or Decimal('0'),
            'avg_price': stats['avg_price'] or Decimal('0'),
            'unique_clients': stats['unique_clients'] or 0,
            'category_breakdown': category_stats
        }
    
    def get_client_revenue_summary(
        self,
        client,
        business_lines: Optional[QuerySet] = None
    ) -> Dict[str, Any]:
        queryset = self.get_queryset().filter(client=client).active()
        if business_lines:
            queryset = queryset.by_business_lines(business_lines)
        stats = queryset.aggregate(
            total_revenue=Sum('price'),
            total_services=Count('id'),
            white_services=Count('id', filter=Q(category='WHITE')),
            black_services=Count('id', filter=Q(category='BLACK')),
            white_revenue=Sum('price', filter=Q(category='WHITE')),
            black_revenue=Sum('price', filter=Q(category='BLACK'))
        )
        return {
            'client': client,
            'total_revenue': stats['total_revenue'] or Decimal('0'),
            'total_services': stats['total_services'] or 0,
            'white_services': stats['white_services'] or 0,
            'black_services': stats['black_services'] or 0,
            'white_revenue': stats['white_revenue'] or Decimal('0'),
            'black_revenue': stats['black_revenue'] or Decimal('0'),
        }
    
    def get_top_clients_by_revenue(
        self,
        business_lines: QuerySet,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        from apps.accounting.models import Client
        clients = Client.objects.filter(
            services__business_line__in=business_lines,
            services__is_active=True
        ).annotate(
            total_revenue=Sum('services__price'),
            total_services=Count('services', distinct=True),
            white_services=Count(
                'services',
                filter=Q(services__category='WHITE', services__is_active=True)
            ),
            black_services=Count(
                'services',
                filter=Q(services__category='BLACK', services__is_active=True)
            )
        ).order_by('-total_revenue')[:limit]
        return [
            {
                'client': client,
                'total_revenue': client.total_revenue or Decimal('0'),
                'total_services': client.total_services or 0,
                'white_services': client.white_services or 0,
                'black_services': client.black_services or 0,
            }
            for client in clients
        ]
    
    def get_services_with_remanentes(self, business_lines: QuerySet) -> QuerySet:
        return self.get_queryset().filter(
            business_line__in=business_lines,
            category='BLACK',
            is_active=True
        ).exclude(
            remanentes__isnull=True
        ).exclude(
            remanentes={}
        ).with_client_data()
    
    def get_revenue_by_payment_method(
        self,
        business_lines: QuerySet
    ) -> Dict[str, Decimal]:
        from apps.accounting.models import ClientService
        revenue_data = {}
        for choice in ClientService.PaymentMethodChoices:
            revenue = self.get_queryset().filter(
                business_line__in=business_lines,
                payment_method=choice.value,
                is_active=True
            ).aggregate(
                total=Sum('price')
            )['total'] or Decimal('0')
            revenue_data[choice.value] = revenue
        return revenue_data
    
    def get_monthly_revenue_trend(
        self,
        business_lines: QuerySet,
        year: int
    ) -> List[Dict[str, Any]]:
        monthly_data = []
        for month in range(1, 13):
            revenue = self.get_queryset().filter(
                business_line__in=business_lines,
                start_date__year=year,
                start_date__month=month,
                is_active=True
            ).aggregate(
                total_revenue=Sum('price'),
                total_services=Count('id')
            )
            monthly_data.append({
                'month': month,
                'total_revenue': revenue['total_revenue'] or Decimal('0'),
                'total_services': revenue['total_services'] or 0
            })
        return monthly_data
