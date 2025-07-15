from django.db.models import Sum, Count, F, Value
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from datetime import timedelta

from apps.accounting.models import ClientService, ServicePayment
from apps.expenses.models import Expense, ExpenseCategory
from apps.business_lines.models import BusinessLine


class DashboardDataService:
    
    @staticmethod
    def get_net_revenue_aggregation():
        from django.db import models
        return Sum(F('amount') - Coalesce(F('refunded_amount'), Value(0, output_field=models.DecimalField())))
    
    @classmethod
    def get_financial_summary(cls):
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        
        net_revenue_agg = cls.get_net_revenue_aggregation()
        
        total_ingresos = ServicePayment.objects.aggregate(total=net_revenue_agg)['total'] or 0
        ingresos_mes = ServicePayment.objects.filter(
            payment_date__gte=start_of_month
        ).aggregate(total=net_revenue_agg)['total'] or 0
        
        total_gastos = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        gastos_mes = Expense.objects.filter(
            date__gte=start_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        resultado_total = total_ingresos - total_gastos
        resultado_mes = ingresos_mes - gastos_mes
        margen_beneficio = (resultado_total / total_ingresos * 100) if total_ingresos > 0 else 0
        ingresos_diarios = ingresos_mes / 30 if ingresos_mes > 0 else 0
        
        return {
            'total_ingresos': total_ingresos,
            'total_gastos': total_gastos,
            'resultado_total': resultado_total,
            'ingresos_mes': ingresos_mes,
            'gastos_mes': gastos_mes,
            'resultado_mes': resultado_mes,
            'margen_beneficio': margen_beneficio,
            'ingresos_diarios': ingresos_diarios,
        }
    
    @classmethod
    def get_temporal_data(cls):
        today = timezone.now().date()
        start_date = today.replace(day=1) - timedelta(days=365)
        
        ingresos_por_mes = ServicePayment.objects.filter(
            payment_date__gte=start_date
        ).annotate(
            mes=TruncMonth('payment_date')
        ).values('mes').annotate(
            total=cls.get_net_revenue_aggregation()
        ).order_by('mes')
        
        gastos_por_mes = Expense.objects.filter(
            date__gte=start_date
        ).annotate(
            mes=TruncMonth('date')
        ).values('mes').annotate(
            total=Sum('amount')
        ).order_by('mes')
        
        ingresos_dict = {item['mes'].strftime('%Y-%m'): float(item['total'] or 0) for item in ingresos_por_mes}
        gastos_dict = {item['mes'].strftime('%Y-%m'): float(item['total'] or 0) for item in gastos_por_mes}
        
        months = []
        current_date = start_date
        while current_date <= today:
            month_key = current_date.strftime('%Y-%m')
            ingresos = ingresos_dict.get(month_key, 0)
            gastos = gastos_dict.get(month_key, 0)
            
            months.append({
                'month': current_date.strftime('%b %Y'),
                'ingresos': ingresos,
                'gastos': gastos,
                'beneficio': ingresos - gastos
            })
            
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return months[-12:]
    
    @classmethod
    def get_business_lines_data(cls):
        business_lines = []
        
        for bl in BusinessLine.objects.filter(parent__isnull=False):
            servicios = ClientService.objects.filter(business_line=bl)
            pagos = ServicePayment.objects.filter(client_service__in=servicios)
            
            ingresos_netos = pagos.aggregate(
                total=cls.get_net_revenue_aggregation()
            )['total'] or 0
            
            business_lines.append({
                'name': bl.name,
                'total_ingresos': ingresos_netos,
                'num_servicios': servicios.count(),
            })
        
        return sorted(business_lines, key=lambda x: x['total_ingresos'], reverse=True)
    
    @staticmethod
    def get_expense_categories_data():
        return ExpenseCategory.objects.annotate(
            total=Sum('expenses__amount'),
            count=Count('expenses')
        ).filter(total__isnull=False).order_by('-total')
