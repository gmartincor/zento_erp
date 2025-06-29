from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import date, timedelta
from django.db import models
from django.db.models import QuerySet, Q, Sum, Count, Avg, F, Case, When, Value
from django.utils import timezone
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
    
    def expiring_soon(self, days=30):
        target_date = timezone.now().date() + timedelta(days=days)
        return self.active().filter(
            end_date__isnull=False,
            end_date__gte=timezone.now().date(),
            end_date__lte=target_date
        )
    
    def expired(self):
        return self.active().filter(
            end_date__isnull=False,
            end_date__lt=timezone.now().date()
        )
    
    def with_status(self, status):
        from datetime import timedelta
        today = timezone.now().date()
        
        base_filter = Q(is_active=True)
        
        if status == 'inactive':
            return self.filter(is_active=False)
        elif status == 'suspended':
            return self.filter(base_filter, admin_status='SUSPENDED')
        elif status == 'expired':
            return self.filter(base_filter, admin_status='ENABLED', end_date__lt=today)
        elif status == 'active':
            return self.filter(
                base_filter & 
                Q(admin_status='ENABLED') &
                (Q(end_date__isnull=True) | Q(end_date__gte=today + timedelta(days=30)))
            )
        elif status == 'renewal_due':
            return self.filter(
                base_filter,
                admin_status='ENABLED', 
                end_date__gte=today + timedelta(days=7),
                end_date__lt=today + timedelta(days=30)
            )
        elif status == 'expiring_soon':
            return self.filter(
                base_filter,
                admin_status='ENABLED',
                end_date__gte=today,
                end_date__lt=today + timedelta(days=7)
            )
        
        return self.none()


class ClientServiceManager(models.Manager):
    def get_queryset(self):
        return ClientServiceQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def by_category(self, category: str):
        return self.get_queryset().by_category(category)
    
    def by_business_line(self, business_line):
        return self.get_queryset().by_business_line(business_line)
    
    def by_business_lines(self, business_lines: QuerySet):
        return self.get_queryset().by_business_lines(business_lines)
    
    def with_payments(self):
        return self.get_queryset().filter(payments__isnull=False).distinct()
    
    def expiring_soon(self, days=30):
        return self.get_queryset().expiring_soon(days)
    
    def expired(self):
        return self.get_queryset().expired()
    
    def with_status(self, status):
        return self.get_queryset().with_status(status)
    
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
        from apps.accounting.models import ServicePayment
        
        queryset = self.get_queryset().by_business_line(business_line).active()
        if category:
            queryset = queryset.by_category(category)
        
        total_services = queryset.count()
        unique_clients = queryset.values('client').distinct().count()
        
        paid_payments = ServicePayment.objects.filter(
            client_service__in=queryset,
            status=ServicePayment.StatusChoices.PAID
        )
        
        revenue_stats = paid_payments.aggregate(
            total_revenue=Sum('amount'),
            avg_payment=Avg('amount')
        )
        
        category_stats = {}
        for cat_choice in queryset.model.CategoryChoices:
            cat_services = queryset.filter(category=cat_choice.value)
            cat_payments = paid_payments.filter(client_service__in=cat_services)
            
            category_stats[cat_choice.value] = {
                'count': cat_services.count(),
                'revenue': cat_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
            }
        
        return {
            'total_services': total_services,
            'total_revenue': revenue_stats['total_revenue'] or Decimal('0'),
            'avg_payment': revenue_stats['avg_payment'] or Decimal('0'),
            'unique_clients': unique_clients,
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
            
        services = queryset
        service_stats = services.aggregate(
            total_services=Count('id'),
            unique_clients=Count('client', distinct=True)
        )
        
        from apps.accounting.models import ServicePayment
        payment_stats = ServicePayment.objects.filter(
            client_service__in=services
        ).aggregate(
            total_revenue=Sum('amount'),
            avg_price=Avg('amount')
        )
        
        category_stats = {
            'WHITE': ServicePayment.objects.filter(
                client_service__in=services.filter(category='WHITE')
            ).aggregate(
                count=Count('client_service__id', distinct=True),
                revenue=Sum('amount')
            ),
            'BLACK': ServicePayment.objects.filter(
                client_service__in=services.filter(category='BLACK')
            ).aggregate(
                count=Count('client_service__id', distinct=True),
                revenue=Sum('amount')
            )
        }
        
        stats = {**service_stats, **payment_stats}
        
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
        services = queryset
        service_stats = services.aggregate(
            total_services=Count('id'),
            white_services=Count('id', filter=Q(category='WHITE')),
            black_services=Count('id', filter=Q(category='BLACK'))
        )
        
        from apps.accounting.models import ServicePayment
        payment_stats = ServicePayment.objects.filter(
            client_service__in=services
        ).aggregate(
            total_revenue=Sum('amount'),
            white_revenue=Sum('amount', filter=Q(client_service__category='WHITE')),
            black_revenue=Sum('amount', filter=Q(client_service__category='BLACK'))
        )
        
        stats = {**service_stats, **payment_stats}
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
        from apps.accounting.models import Client, ServicePayment
        
        # Get clients that have services in the specified business lines
        clients_with_services = Client.objects.filter(
            services__business_line__in=business_lines,
            services__is_active=True
        ).distinct()
        
        client_data = []
        for client in clients_with_services:
            services = client.services.filter(
                business_line__in=business_lines,
                is_active=True
            )
            
            service_stats = services.aggregate(
                total_services=Count('id'),
                white_services=Count('id', filter=Q(category='WHITE')),
                black_services=Count('id', filter=Q(category='BLACK'))
            )
            
            revenue_stats = ServicePayment.objects.filter(
                client_service__in=services
            ).aggregate(
                total_revenue=Sum('amount')
            )
            
            client_data.append({
                'client': client,
                'total_revenue': revenue_stats['total_revenue'] or Decimal('0'),
                'total_services': service_stats['total_services'] or 0,
                'white_services': service_stats['white_services'] or 0,
                'black_services': service_stats['black_services'] or 0,
            })
        
        # Sort by revenue and limit
        client_data.sort(key=lambda x: x['total_revenue'], reverse=True)
        return client_data[:limit]
    
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
        from apps.accounting.models import ServicePayment
        
        revenue_data = {}
        services = self.get_queryset().filter(business_line__in=business_lines, is_active=True)
        
        for method_choice in ServicePayment.PaymentMethodChoices:
            revenue = ServicePayment.objects.filter(
                client_service__in=services,
                payment_method=method_choice.value,
                status=ServicePayment.StatusChoices.PAID
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            revenue_data[method_choice.value] = revenue
        
        return revenue_data
    
    def get_monthly_revenue_trend(
        self,
        business_lines: QuerySet,
        year: int
    ) -> List[Dict[str, Any]]:
        from apps.accounting.models import ServicePayment
        
        monthly_data = []
        services = self.get_queryset().filter(business_line__in=business_lines)
        
        for month in range(1, 13):
            payments = ServicePayment.objects.filter(
                client_service__in=services,
                payment_date__year=year,
                payment_date__month=month,
                status=ServicePayment.StatusChoices.PAID
            )
            
            revenue_stats = payments.aggregate(
                total_revenue=Sum('amount'),
                total_payments=Count('id')
            )
            
            monthly_data.append({
                'month': month,
                'total_revenue': revenue_stats['total_revenue'] or Decimal('0'),
                'total_payments': revenue_stats['total_payments'] or 0
            })
        
        return monthly_data

    def get_services_by_status(self, business_lines: QuerySet) -> Dict[str, int]:
        services = self.get_queryset().filter(business_line__in=business_lines)
        
        status_counts = {
            'ACTIVE': 0,
            'INACTIVE': 0,
            'EXPIRED_RECENT': 0,
            'EXPIRED': 0
        }
        
        for service in services:
            status_counts[service.current_status] += 1
        
        return status_counts

    def get_expiring_services(self, business_lines: QuerySet, days_ahead: int = 30) -> QuerySet:
        from apps.accounting.services.payment_service import PaymentService
        
        expiring_data = PaymentService.get_expiring_services(days_ahead)
        service_ids = [service.id for service, _ in expiring_data 
                      if service.business_line_id in business_lines.values_list('id', flat=True)]
        
        return self.get_queryset().filter(id__in=service_ids).with_client_data()

    def get_service_history_for_client(
        self,
        client,
        business_line=None,
        category=None,
        active_only=True
    ) -> QuerySet:
        queryset = self.get_queryset().filter(client=client)
        
        if business_line:
            queryset = queryset.filter(business_line=business_line)
        if category:
            queryset = queryset.filter(category=category)
        if active_only:
            queryset = queryset.active()
            
        return queryset.with_client_data().order_by('-created')
