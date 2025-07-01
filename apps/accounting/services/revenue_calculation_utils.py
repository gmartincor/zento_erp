from django.db import models
from django.db.models import F, Sum, Count, Avg, Case, When, Value, DecimalField, Q
from django.db.models.functions import Coalesce


class RevenueCalculationMixin:
    @staticmethod
    def get_net_amount_expression():
        return F('amount') - Coalesce(F('refunded_amount'), Value(0, output_field=DecimalField()))
    
    @staticmethod
    def get_net_revenue_aggregation():
        return Sum(RevenueCalculationMixin.get_net_amount_expression())
    
    @staticmethod
    def get_net_revenue_with_filter(filter_condition):
        return Sum(
            RevenueCalculationMixin.get_net_amount_expression(),
            filter=filter_condition
        )
    
    @staticmethod
    def get_avg_net_revenue_aggregation():
        return Avg(RevenueCalculationMixin.get_net_amount_expression())


class RevenueCalculationUtils:
    @staticmethod
    def calculate_payment_stats(payments_queryset, include_refunds=True):
        if include_refunds:
            stats = payments_queryset.aggregate(
                total_revenue=RevenueCalculationMixin.get_net_revenue_aggregation(),
                payment_count=Count('id'),
                avg_payment=RevenueCalculationMixin.get_avg_net_revenue_aggregation(),
                total_gross_revenue=Sum('amount'),
                total_refunded=Sum('refunded_amount')
            )
        else:
            stats = payments_queryset.aggregate(
                total_revenue=Sum('amount'),
                payment_count=Count('id'),
                avg_payment=Avg('amount'),
                total_gross_revenue=Sum('amount'),
                total_refunded=Sum('refunded_amount')
            )
        
        for key, value in stats.items():
            if value is None:
                stats[key] = 0
        
        return stats
    
    @staticmethod
    def calculate_category_revenue_stats(payments_queryset, categories, include_refunds=True):
        category_stats = {}
        
        for category in categories:
            if include_refunds:
                category_stats[f'{category.lower()}_revenue'] = RevenueCalculationMixin.get_net_revenue_with_filter(
                    filter_condition=Q(client_service__category=category)
                )
            else:
                category_stats[f'{category.lower()}_revenue'] = Sum(
                    'amount', 
                    filter=Q(client_service__category=category)
                )
        
        result = payments_queryset.aggregate(**category_stats)
        
        for key, value in result.items():
            if value is None:
                result[key] = 0
        
        return result
