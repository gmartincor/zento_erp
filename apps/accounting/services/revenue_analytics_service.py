from typing import Dict, Any, Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

from apps.accounting.models import ServicePayment, ClientService
from .revenue_calculation_utils import RevenueCalculationMixin


class RevenueAnalyticsService(RevenueCalculationMixin):
    
    class PeriodType:
        CURRENT_MONTH = 'current_month'
        LAST_MONTH = 'last_month'
        CURRENT_YEAR = 'current_year'
        LAST_YEAR = 'last_year'
        ALL_TIME = 'all_time'
        CUSTOM = 'custom'
        LAST_12_MONTHS = 'last_12_months'
        LAST_6_MONTHS = 'last_6_months'
        LAST_3_MONTHS = 'last_3_months'
    
    def __init__(self):
        self.today = timezone.now().date()
    
    def get_business_line_revenue_summary(
        self, 
        business_line, 
        category: Optional[str] = None,
        period_type: str = PeriodType.ALL_TIME,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        
        services_query = ClientService.objects.filter(
            business_line=business_line,
            is_active=True
        )
        
        if category:
            services_query = services_query.filter(category=category)
        
        payments_query = ServicePayment.objects.filter(
            client_service__in=services_query,
            status=ServicePayment.StatusChoices.PAID
        )
        
        payments_query = self._apply_period_filter(
            payments_query, period_type, start_date, end_date
        )
        
        revenue_stats = payments_query.aggregate(
            total_revenue=self.get_net_revenue_aggregation(),
            payment_count=Count('id'),
            avg_payment=self.get_avg_net_revenue_aggregation()
        )
        
        period_info = self._get_period_description(period_type, start_date, end_date)
        
        return {
            'period': period_info,
            'total_revenue': revenue_stats['total_revenue'] or Decimal('0'),
            'payment_count': revenue_stats['payment_count'] or 0,
            'avg_payment': revenue_stats['avg_payment'] or Decimal('0'),
            'service_count': services_query.count(),
            'avg_revenue_per_service': self._calculate_avg_revenue_per_service(
                revenue_stats['total_revenue'], services_query.count()
            )
        }
    
    def get_service_revenue_breakdown(
        self, 
        client_service: ClientService,
        period_type: str = PeriodType.ALL_TIME,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        
        payments_query = client_service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        )
        
        payments_query = self._apply_period_filter(
            payments_query, period_type, start_date, end_date
        )
        
        payments_list = list(payments_query.order_by('-payment_date'))
        
        revenue_stats = payments_query.aggregate(
            total_revenue=self.get_net_revenue_aggregation(),
            payment_count=Count('id'),
            avg_payment=self.get_avg_net_revenue_aggregation()
        )
        
        period_info = self._get_period_description(period_type, start_date, end_date)
        
        current_payment = client_service.payments.filter(
            status=ServicePayment.StatusChoices.PAID
        ).order_by('-created').first()
        
        return {
            'period': period_info,
            'current_pricing': {
                'amount': current_payment.amount if current_payment else Decimal('0'),
                'payment_method': current_payment.get_payment_method_display() if current_payment else 'No definido',
                'period_start': current_payment.period_start if current_payment else None,
                'period_end': current_payment.period_end if current_payment else None,
            },
            'revenue_summary': {
                'total_revenue': revenue_stats['total_revenue'] or Decimal('0'),
                'payment_count': revenue_stats['payment_count'] or 0,
                'avg_payment': revenue_stats['avg_payment'] or Decimal('0'),
            },
            'payments_history': [
                {
                    'amount': payment.amount,
                    'payment_date': payment.payment_date,
                    'period_start': payment.period_start,
                    'period_end': payment.period_end,
                    'payment_method': payment.get_payment_method_display(),
                    'status': payment.get_status_display(),
                }
                for payment in payments_list
            ]
        }
    
    def get_period_comparison(
        self,
        business_line,
        category: Optional[str] = None,
        compare_periods: List[str] = None
    ) -> Dict[str, Any]:
        
        if not compare_periods:
            compare_periods = [
                self.PeriodType.CURRENT_MONTH,
                self.PeriodType.LAST_MONTH,
                self.PeriodType.CURRENT_YEAR,
                self.PeriodType.LAST_YEAR
            ]
        
        comparison_data = {}
        
        for period in compare_periods:
            stats = self.get_business_line_revenue_summary(
                business_line, category, period
            )
            comparison_data[period] = stats
        
        return comparison_data
    
    def _apply_period_filter(
        self, 
        queryset, 
        period_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ):
        
        if period_type == self.PeriodType.CUSTOM and start_date and end_date:
            return queryset.filter(payment_date__range=[start_date, end_date])
        
        period_dates = self._get_period_dates(period_type)
        if period_dates:
            start, end = period_dates
            return queryset.filter(payment_date__range=[start, end])
        
        return queryset
    
    def _get_period_dates(self, period_type: str) -> Optional[tuple]:
        
        if period_type == self.PeriodType.CURRENT_MONTH:
            start = self.today.replace(day=1)
            end = self.today
            return (start, end)
        
        elif period_type == self.PeriodType.LAST_MONTH:
            last_month = self.today.replace(day=1) - timedelta(days=1)
            start = last_month.replace(day=1)
            end = last_month
            return (start, end)
        
        elif period_type == self.PeriodType.CURRENT_YEAR:
            start = self.today.replace(month=1, day=1)
            end = self.today
            return (start, end)
        
        elif period_type == self.PeriodType.LAST_YEAR:
            last_year = self.today.year - 1
            start = date(last_year, 1, 1)
            end = date(last_year, 12, 31)
            return (start, end)
        
        elif period_type == self.PeriodType.LAST_12_MONTHS:
            start = self.today - timedelta(days=365)
            end = self.today
            return (start, end)
        
        elif period_type == self.PeriodType.LAST_6_MONTHS:
            start = self.today - timedelta(days=180)
            end = self.today
            return (start, end)
        
        elif period_type == self.PeriodType.LAST_3_MONTHS:
            start = self.today - timedelta(days=90)
            end = self.today
            return (start, end)
        
        return None
    
    def _get_period_description(
        self, 
        period_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        
        descriptions = {
            self.PeriodType.CURRENT_MONTH: f"Mes actual ({self.today.strftime('%B %Y')})",
            self.PeriodType.LAST_MONTH: "Mes anterior",
            self.PeriodType.CURRENT_YEAR: f"Año actual ({self.today.year})",
            self.PeriodType.LAST_YEAR: f"Año anterior ({self.today.year - 1})",
            self.PeriodType.ALL_TIME: "Histórico total",
            self.PeriodType.LAST_12_MONTHS: "Últimos 12 meses",
            self.PeriodType.LAST_6_MONTHS: "Últimos 6 meses",
            self.PeriodType.LAST_3_MONTHS: "Últimos 3 meses",
        }
        
        if period_type == self.PeriodType.CUSTOM and start_date and end_date:
            description = f"Período personalizado ({start_date} - {end_date})"
        else:
            description = descriptions.get(period_type, "Período no especificado")
        
        period_dates = self._get_period_dates(period_type)
        if period_dates:
            start, end = period_dates
        elif period_type == self.PeriodType.CUSTOM:
            start, end = start_date, end_date
        else:
            start, end = None, None
        
        return {
            'type': period_type,
            'description': description,
            'start_date': start,
            'end_date': end,
        }
    
    def _calculate_avg_revenue_per_service(self, total_revenue: Optional[Decimal], service_count: int) -> Decimal:
        if not total_revenue or service_count == 0:
            return Decimal('0')
        return total_revenue / service_count
