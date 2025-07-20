from typing import Dict, Any, Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from calendar import month_name

from apps.accounting.models import ServicePayment, ClientService
from apps.expenses.models import Expense
from apps.business_lines.models import BusinessLine
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

    def get_temporal_financial_overview(self, months: int = 12) -> Dict[str, Any]:
        """Obtiene datos financieros temporales para dashboard"""
        end_date = self.today
        start_date = end_date - timedelta(days=30 * months)
        
        monthly_data = []
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            month_end = min(next_month - timedelta(days=1), end_date)
            
            month_stats = self._get_month_financial_data(current_date, month_end)
            monthly_data.append({
                'period': current_date.strftime('%Y-%m'),
                'month_name': month_name[current_date.month],
                'year': current_date.year,
                **month_stats
            })
            
            current_date = next_month
            
        return {
            'temporal_data': monthly_data,
            'summary': self._calculate_temporal_summary(monthly_data)
        }

    def get_expense_categories_breakdown(self, period_months: int = 12) -> Dict[str, Any]:
        """Distribución de gastos por categorías"""
        from apps.expenses.models import ExpenseCategory
        
        end_date = self.today
        start_date = end_date - timedelta(days=30 * period_months)
        
        expenses = Expense.objects.filter(
            date__range=[start_date, end_date]
        ).select_related('category')
        
        category_data = expenses.values(
            'category__name',
            'category__category_type'
        ).annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('-total_amount')
        
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        categories = []
        for item in category_data:
            amount = item['total_amount']
            percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
            categories.append({
                'name': item['category__name'],
                'type': item['category__category_type'],
                'amount': amount,
                'count': item['count'],
                'percentage': round(percentage, 2)
            })
            
        return {
            'categories': categories,
            'total_amount': total_expenses,
            'period_months': period_months
        }

    def get_business_lines_performance(self, period_months: int = 12) -> Dict[str, Any]:
        """Performance por líneas de negocio"""
        end_date = self.today
        start_date = end_date - timedelta(days=30 * period_months)
        
        business_lines = BusinessLine.objects.filter(
            parent__isnull=False,
            is_active=True
        ).prefetch_related('client_services')
        
        lines_data = []
        for line in business_lines:
            services = line.client_services.filter(is_active=True)
            
            payments = ServicePayment.objects.filter(
                client_service__in=services,
                payment_date__range=[start_date, end_date],
                status=ServicePayment.StatusChoices.PAID
            )
            
            revenue_stats = payments.aggregate(
                total_revenue=self.get_net_revenue_aggregation(),
                payment_count=Count('id')
            )
            
            lines_data.append({
                'name': line.name,
                'level': line.level,
                'total_revenue': revenue_stats['total_revenue'] or Decimal('0'),
                'payment_count': revenue_stats['payment_count'] or 0,
                'service_count': services.count(),
                'avg_revenue_per_service': self._calculate_avg_revenue_per_service(
                    revenue_stats['total_revenue'], services.count()
                )
            })
            
        lines_data.sort(key=lambda x: x['total_revenue'], reverse=True)
        
        return {
            'business_lines': lines_data,
            'period_months': period_months,
            'total_lines': len(lines_data)
        }

    def get_client_metrics_overview(self, period_months: int = 12) -> Dict[str, Any]:
        """Métricas de clientes para dashboard"""
        end_date = self.today
        start_date = end_date - timedelta(days=30 * period_months)
        
        active_services = ClientService.objects.filter(is_active=True)
        period_payments = ServicePayment.objects.filter(
            payment_date__range=[start_date, end_date],
            status=ServicePayment.StatusChoices.PAID
        )
        
        client_stats = {
            'active_clients': active_services.values('client').distinct().count(),
            'total_services': active_services.count(),
            'period_revenue': period_payments.aggregate(
                total=self.get_net_revenue_aggregation()
            )['total'] or Decimal('0'),
            'period_payments': period_payments.count()
        }
        
        if client_stats['active_clients'] > 0:
            client_stats['avg_revenue_per_client'] = (
                client_stats['period_revenue'] / client_stats['active_clients']
            )
        else:
            client_stats['avg_revenue_per_client'] = Decimal('0')
            
        if client_stats['period_payments'] > 0:
            client_stats['avg_payment_amount'] = (
                client_stats['period_revenue'] / client_stats['period_payments']
            )
        else:
            client_stats['avg_payment_amount'] = Decimal('0')
            
        return client_stats

    def _get_month_financial_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Datos financieros para un mes específico"""
        payments = ServicePayment.objects.filter(
            payment_date__range=[start_date, end_date],
            status=ServicePayment.StatusChoices.PAID
        )
        
        expenses = Expense.objects.filter(
            date__range=[start_date, end_date]
        )
        
        revenue_stats = payments.aggregate(
            total_revenue=self.get_net_revenue_aggregation(),
            payment_count=Count('id')
        )
        
        expense_stats = expenses.aggregate(
            total_expenses=Sum('amount'),
            expense_count=Count('id')
        )
        
        total_revenue = revenue_stats['total_revenue'] or Decimal('0')
        total_expenses = expense_stats['total_expenses'] or Decimal('0')
        profit = total_revenue - total_expenses
        
        profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        
        return {
            'revenue': total_revenue,
            'expenses': total_expenses,
            'profit': profit,
            'profit_margin': round(profit_margin, 2),
            'payment_count': revenue_stats['payment_count'] or 0,
            'expense_count': expense_stats['expense_count'] or 0
        }

    def _calculate_temporal_summary(self, monthly_data: List[Dict]) -> Dict[str, Any]:
        """Calcula resumen de datos temporales"""
        if not monthly_data:
            return {}
            
        total_revenue = sum(month['revenue'] for month in monthly_data)
        total_expenses = sum(month['expenses'] for month in monthly_data)
        total_profit = total_revenue - total_expenses
        
        avg_monthly_revenue = total_revenue / len(monthly_data) if monthly_data else Decimal('0')
        avg_monthly_expenses = total_expenses / len(monthly_data) if monthly_data else Decimal('0')
        
        revenue_growth = self._calculate_growth_rate(monthly_data, 'revenue')
        profit_growth = self._calculate_growth_rate(monthly_data, 'profit')
        
        best_month = max(monthly_data, key=lambda x: x['profit']) if monthly_data else {}
        worst_month = min(monthly_data, key=lambda x: x['profit']) if monthly_data else {}
        
        return {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'total_profit': total_profit,
            'avg_monthly_revenue': avg_monthly_revenue,
            'avg_monthly_expenses': avg_monthly_expenses,
            'revenue_growth_rate': revenue_growth,
            'profit_growth_rate': profit_growth,
            'best_month': best_month,
            'worst_month': worst_month,
            'months_analyzed': len(monthly_data)
        }

    def _calculate_growth_rate(self, monthly_data: List[Dict], metric: str) -> Decimal:
        """Calcula tasa de crecimiento para una métrica"""
        if len(monthly_data) < 2:
            return Decimal('0')
            
        first_value = monthly_data[0][metric]
        last_value = monthly_data[-1][metric]
        
        if first_value == 0:
            return Decimal('100') if last_value > 0 else Decimal('0')
            
        growth = ((last_value - first_value) / first_value) * 100
        return round(growth, 2)

    def get_business_line_revenue_summary(
        self, 
        business_line, 
        category: Optional[str] = None,
        period_type: str = PeriodType.ALL_TIME,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        
        # Obtener IDs de la línea y todos sus descendientes
        line_descendant_ids = business_line.get_descendant_ids()
        
        services_query = ClientService.objects.filter(
            business_line__id__in=line_descendant_ids,
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
