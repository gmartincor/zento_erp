from decimal import Decimal
from django.db.models import Q, Sum, Count, Avg, QuerySet
from django.utils import timezone
from datetime import datetime, timedelta

from apps.business_lines.models import BusinessLine
from apps.accounting.models import ClientService, ServicePayment
from .revenue_calculation_utils import RevenueCalculationMixin, RevenueCalculationUtils


class StatisticsService(RevenueCalculationMixin):
    def calculate_business_line_stats(self, business_line, include_children=True):
        services_query = self._get_services_for_line(business_line, include_children)
        
        paid_payments = ServicePayment.objects.filter(
            client_service__in=services_query,
            status=ServicePayment.StatusChoices.PAID
        )
        
        stats = paid_payments.aggregate(
            total_revenue=self.get_net_revenue_aggregation(),
            total_payments=Count('id')
        )
        
        service_stats = services_query.aggregate(
            total_services=Count('id'),
            white_services=Count('id', filter=Q(category='WHITE')),
            black_services=Count('id', filter=Q(category='BLACK')),
            unique_clients=Count('client', distinct=True)
        )
        
        category_revenue = {
            'white_revenue': paid_payments.filter(
                client_service__category='WHITE'
            ).aggregate(total=self.get_net_revenue_aggregation())['total'] or Decimal('0'),
            'black_revenue': paid_payments.filter(
                client_service__category='BLACK'
            ).aggregate(total=self.get_net_revenue_aggregation())['total'] or Decimal('0')
        }
        
        total_remanentes = self._calculate_remanente_totals(
            services_query.filter(category='BLACK')
        )
        
        combined_stats = {**stats, **service_stats, **category_revenue}
        return self._normalize_stats(combined_stats, total_remanentes)
    
    def get_revenue_summary_by_period(self, business_lines, year=None, month=None):
        services_query = ClientService.objects.filter(
            business_line__in=business_lines,
            is_active=True
        )
        
        payments_query = ServicePayment.objects.filter(
            client_service__in=services_query,
            status=ServicePayment.StatusChoices.PAID
        )
        
        payments_query = self._apply_payment_date_filters(payments_query, year, month)
        
        period_stats = payments_query.aggregate(
            total_revenue=self.get_net_revenue_aggregation(),
            total_payments=Count('id')
        )
        
        service_stats = services_query.aggregate(
            total_services=Count('id'),
            unique_clients=Count('client', distinct=True)
        )
        
        category_revenue = {
            'white_revenue': payments_query.filter(
                client_service__category='WHITE'
            ).aggregate(total=self.get_net_revenue_aggregation())['total'] or Decimal('0'),
            'black_revenue': payments_query.filter(
                client_service__category='BLACK'
            ).aggregate(total=self.get_net_revenue_aggregation())['total'] or Decimal('0')
        }
        
        period_info = self._get_period_info(year, month)
        combined_stats = {**period_stats, **service_stats, **category_revenue}
        
        return {
            **self._normalize_basic_stats(combined_stats),
            'period_info': period_info,
            'business_lines_count': business_lines.count()
        }
    
    def calculate_category_performance(self, category, business_lines):
        services_query = ClientService.objects.filter(
            business_line__in=business_lines,
            category=category,
            is_active=True
        )
        
        payments_query = ServicePayment.objects.filter(
            client_service__in=services_query,
            status=ServicePayment.StatusChoices.PAID
        )
        
        stats = payments_query.aggregate(
            total_revenue=self.get_net_revenue_aggregation(),
            payment_count=Count('id'),
            avg_payment=self.get_avg_net_revenue_aggregation()
        )
        
        service_stats = services_query.aggregate(
            service_count=Count('id'),
            unique_clients=Count('client', distinct=True)
        )
        
        combined_stats = {**stats, **service_stats}
        
        if category == 'BLACK':
            combined_stats['total_remanentes'] = self._calculate_remanente_totals(services_query)
        
        return self._normalize_basic_stats(combined_stats)
    
    def get_client_performance_analysis(self, business_lines, limit=10):
        services_query = ClientService.objects.filter(
            business_line__in=business_lines, 
            is_active=True
        )
        
        top_clients = (
            ServicePayment.objects
            .filter(
                client_service__in=services_query,
                status=ServicePayment.StatusChoices.PAID
            )
            .values(
                'client_service__client__id', 
                'client_service__client__full_name', 
                'client_service__client__dni'
            )
            .annotate(
                total_revenue=self.get_net_revenue_aggregation(),
                payment_count=Count('id'),
                avg_payment=self.get_avg_net_revenue_aggregation()
            )
            .order_by('-total_revenue')[:limit]
        )
        
        client_stats = self._calculate_client_distribution_stats(business_lines)
        return {
            'top_clients': list(top_clients),
            'client_stats': client_stats
        }
    
    def compare_periods(self, business_lines, current_year, current_month, 
                       previous_year=None, previous_month=None):
        current_stats = self.get_revenue_summary_by_period(
            business_lines, current_year, current_month
        )
        if previous_year is None or previous_month is None:
            prev_date = datetime(current_year, current_month, 1) - timedelta(days=1)
            previous_year = prev_date.year
            previous_month = prev_date.month
        previous_stats = self.get_revenue_summary_by_period(
            business_lines, previous_year, previous_month
        )
        revenue_change = self._calculate_percentage_change(
            previous_stats['total_revenue'],
            current_stats['total_revenue']
        )
        service_change = self._calculate_percentage_change(
            previous_stats['total_services'],
            current_stats['total_services']
        )
        return {
            'current_period': current_stats,
            'previous_period': previous_stats,
            'revenue_change': revenue_change,
            'service_change': service_change
        }
    
    def calculate_remanente_stats(self, business_line=None, client_service=None):
        """Calcula estadísticas de remanentes usando el campo simple"""
        if client_service:
            query = ServicePayment.objects.filter(client_service=client_service)
        elif business_line:
            services = self._get_services_for_line(business_line, include_children=True)
            query = ServicePayment.objects.filter(client_service__in=services)
        else:
            return {'total_amount': Decimal('0'), 'total_count': 0, 'average_amount': Decimal('0'), 'has_remanentes': False}
        
        remanentes = query.filter(remanente__isnull=False)
        stats = remanentes.aggregate(
            total_amount=Sum('remanente'),
            total_count=Count('id'),
            average_amount=Avg('remanente')
        )
        
        return {
            'total_amount': stats['total_amount'] or Decimal('0'),
            'total_count': stats['total_count'] or 0,
            'average_amount': stats['average_amount'] or Decimal('0'),
            'has_remanentes': (stats['total_count'] or 0) > 0
        }
    
    def get_service_remanente_summary(self, client_service):
        """Resumen de remanentes para un servicio específico"""
        return self.calculate_remanente_stats(client_service=client_service)

    def _get_services_for_line(self, business_line, include_children):
        if include_children:
            line_ids = [business_line.id]
            self._collect_descendant_ids(business_line, line_ids)
            return ClientService.objects.filter(
                business_line_id__in=line_ids,
                is_active=True
            )
        else:
            return ClientService.objects.filter(
                business_line=business_line,
                is_active=True
            )
    
    def _collect_descendant_ids(self, business_line, id_list):
        for child in business_line.children.filter(is_active=True):
            id_list.append(child.id)
            self._collect_descendant_ids(child, id_list)
    
    def _calculate_remanente_totals(self, services_query):
        """Calcula totales de remanentes usando el campo simple en ServicePeriod"""
        total = ServicePayment.objects.filter(
            client_service__in=services_query,
            remanente__isnull=False
        ).aggregate(total=Sum('remanente'))['total'] or Decimal('0')
        
        return total
    
    def _normalize_stats(self, stats, total_remanentes):
        total_revenue = stats['total_revenue'] or Decimal('0')
        total_services = stats['total_services'] or 0
        return {
            'total_revenue': total_revenue,
            'total_services': total_services,
            'unique_clients': stats['unique_clients'] or 0,
            'white_services': stats['white_services'] or 0,
            'black_services': stats['black_services'] or 0,
            'white_revenue': stats['white_revenue'] or Decimal('0'),
            'black_revenue': stats['black_revenue'] or Decimal('0'),
            'avg_price': stats['avg_price'] or Decimal('0'),
            'total_remanentes': total_remanentes,
            'avg_revenue_per_service': total_revenue / max(total_services, 1)
        }
    
    def _normalize_basic_stats(self, stats):
        return {
            'total_revenue': stats.get('total_revenue') or Decimal('0'),
            'total_services': stats.get('total_services') or stats.get('service_count', 0),
            'white_revenue': stats.get('white_revenue') or Decimal('0'),
            'black_revenue': stats.get('black_revenue') or Decimal('0'),
            'unique_clients': stats.get('unique_clients') or 0,
            'avg_price': stats.get('avg_price') or Decimal('0'),
            'total_remanentes': stats.get('total_remanentes') or Decimal('0')
        }
    
    def _apply_payment_date_filters(self, payments_query, year=None, month=None):
        if year:
            payments_query = payments_query.filter(payment_date__year=year)
        if month:
            payments_query = payments_query.filter(payment_date__month=month)
        return payments_query
    
    def _get_period_info(self, year, month):
        now = timezone.now()
        return {
            'year': year or now.year,
            'month': month or now.month,
            'is_current_month': (year == now.year and month == now.month) if year and month else False
        }
    
    def _calculate_client_distribution_stats(self, business_lines):
        stats = (
            ClientService.objects
            .filter(business_line__in=business_lines, is_active=True)
            .aggregate(
                total_clients=Count('client', distinct=True),
                total_services=Count('id'),
                avg_services_per_client=Avg('client__services__id')
            )
        )
        return self._normalize_basic_stats(stats)
    
    def _calculate_percentage_change(self, old_value, new_value):
        if not old_value or old_value == 0:
            return 100 if new_value else 0
        return ((new_value - old_value) / old_value) * 100
