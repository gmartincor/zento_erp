from typing import List, Dict, Optional, Any
from django.db import models
from django.db.models import QuerySet, Q, Sum, Count, F, Value
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()

def get_net_revenue_aggregation():
    return Sum(F('amount') - Coalesce(F('refunded_amount'), Value(0, output_field=models.DecimalField())))

def get_net_revenue_with_filter(filter_condition):
    return Sum(
        F('amount') - Coalesce(F('refunded_amount'), Value(0, output_field=models.DecimalField())),
        filter=filter_condition
    )


class BusinessLineQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)
    
    def roots(self):
        return self.filter(level=1)
    
    def children_of(self, parent):
        return self.filter(parent=parent)
    
    def with_service_counts(self):
        return self.annotate(
            total_services=Count(
                'client_services',
                filter=Q(client_services__is_active=True)
            ),
            white_services=Count(
                'client_services',
                filter=Q(
                    client_services__category='WHITE',
                    client_services__is_active=True
                )
            ),
            black_services=Count(
                'client_services',
                filter=Q(
                    client_services__category='BLACK',
                    client_services__is_active=True
                )
            ),
            total_revenue=Sum(
                'client_services__payments__amount',
                filter=Q(
                    client_services__is_active=True,
                    client_services__payments__status='PAID'
                )
            )
        )


class BusinessLineManager(models.Manager):
    def get_queryset(self):
        return BusinessLineQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def roots(self):
        return self.get_queryset().roots()
    
    def get_accessible_lines_for_user(self, user):
        return self.active()
    
    def get_root_lines_for_user(self, user):
        return self.roots().active().with_service_counts().order_by('name')
    
    def get_line_by_path(self, line_path: str):
        if not line_path:
            raise ObjectDoesNotExist("Empty path provided")
        path_parts = line_path.strip('/').split('/')
        if len(path_parts) == 1:
            return self.get(slug=path_parts[0], level=1, is_active=True)
        current_line = None
        for i, slug in enumerate(path_parts):
            if i == 0:
                current_line = self.get(slug=slug, level=1, is_active=True)
            else:
                current_line = self.get(
                    slug=slug,
                    parent=current_line,
                    is_active=True
                )
        return current_line
    
    def get_children_for_display(
        self,
        business_line,
        accessible_lines: QuerySet
    ) -> QuerySet:
        children = self.get_queryset().filter(
            parent=business_line,
            id__in=accessible_lines
        ).active().with_service_counts().order_by('name')
        return children
    
    def get_hierarchy_path(self, business_line) -> List[Dict[str, Any]]:
        path = []
        current = business_line
        while current:
            path.insert(0, {
                'id': current.id,
                'name': current.name,
                'slug': current.slug,
                'level': current.level
            })
            current = current.parent
        return path
    
    def get_business_lines_with_services(
        self,
        accessible_lines: QuerySet
    ) -> QuerySet:
        return accessible_lines.filter(
            client_services__is_active=True
        ).distinct().with_service_counts()
    
    def search_business_lines(
        self,
        query: str,
        accessible_lines: QuerySet
    ) -> QuerySet:
        return accessible_lines.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(slug__icontains=query)
        ).with_service_counts()
    
    def get_business_line_statistics(
        self,
        business_line,
        include_descendants: bool = True
    ) -> Dict[str, Any]:
        from apps.accounting.models import ClientService, ServicePayment
        
        if include_descendants:
            descendant_ids = business_line.get_descendant_ids()
            services_filter = Q(business_line_id__in=descendant_ids, is_active=True)
        else:
            services_filter = Q(business_line=business_line, is_active=True)
        
        services = ClientService.objects.filter(services_filter)
        service_stats = services.aggregate(
            total_services=Count('id'),
            unique_clients=Count('client', distinct=True),
            white_services=Count('id', filter=Q(category='WHITE')),
            black_services=Count('id', filter=Q(category='BLACK')),
        )
        
        payment_stats = ServicePayment.objects.filter(
            client_service__in=services
        ).aggregate(
            total_revenue=get_net_revenue_aggregation(),
            white_revenue=get_net_revenue_with_filter(Q(client_service__category='WHITE')),
            black_revenue=get_net_revenue_with_filter(Q(client_service__category='BLACK'))
        )
        
        stats = {**service_stats, **payment_stats}
        
        return {
            'business_line': business_line,
            'total_services': stats['total_services'] or 0,
            'total_revenue': stats['total_revenue'] or 0,
            'unique_clients': stats['unique_clients'] or 0,
            'white_services': stats['white_services'] or 0,
            'black_services': stats['black_services'] or 0,
            'white_revenue': stats['white_revenue'] or 0,
            'black_revenue': stats['black_revenue'] or 0,
            'include_descendants': include_descendants
        }
