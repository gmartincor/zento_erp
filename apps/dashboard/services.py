from django.db.models import Sum, Count, F, Value, Q
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from datetime import timedelta

from apps.accounting.models import ClientService, ServicePayment
from apps.expenses.models import Expense, ExpenseCategory
from apps.business_lines.models import BusinessLine
from apps.accounting.services.business_line_service import BusinessLineService


class DashboardDataService:
    
    BUSINESS_CATEGORY = 'business'
    
    @staticmethod
    def get_net_revenue_aggregation():
        from django.db import models
        return Sum(F('amount') - Coalesce(F('refunded_amount'), Value(0, output_field=models.DecimalField())))
    
    @classmethod
    def get_business_expenses_queryset(cls):
        return Expense.objects.filter(service_category=cls.BUSINESS_CATEGORY)
    
    @classmethod
    def get_business_payments_queryset(cls):
        active_lines = BusinessLine.objects.filter(is_active=True)
        all_descendant_ids = set()
        for line in active_lines:
            all_descendant_ids.update(line.get_descendant_ids())
        
        business_services = ClientService.objects.filter(
            business_line__id__in=all_descendant_ids,
            category=cls.BUSINESS_CATEGORY
        )
        return ServicePayment.objects.filter(client_service__in=business_services)
    
    @classmethod
    def get_business_expense_categories_queryset(cls):
        return ExpenseCategory.objects.filter(
            expenses__service_category=cls.BUSINESS_CATEGORY
        ).distinct()
    
    @classmethod
    def get_financial_summary(cls):
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        
        net_revenue_agg = cls.get_net_revenue_aggregation()
        business_payments = cls.get_business_payments_queryset()
        business_expenses = cls.get_business_expenses_queryset()
        
        total_ingresos = business_payments.aggregate(total=net_revenue_agg)['total'] or 0
        ingresos_mes = business_payments.filter(
            payment_date__gte=start_of_month
        ).aggregate(total=net_revenue_agg)['total'] or 0
        
        total_gastos = business_expenses.aggregate(total=Sum('amount'))['total'] or 0
        gastos_mes = business_expenses.filter(
            date__gte=start_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        resultado_total = total_ingresos - total_gastos
        resultado_mes = ingresos_mes - gastos_mes
        margen_beneficio = (resultado_total / total_ingresos * 100) if total_ingresos > 0 else 0
        margen_beneficio_mes = (resultado_mes / ingresos_mes * 100) if ingresos_mes > 0 else 0
        
        return {
            'total_ingresos': total_ingresos,
            'total_gastos': total_gastos,
            'resultado_total': resultado_total,
            'ingresos_mes': ingresos_mes,
            'gastos_mes': gastos_mes,
            'resultado_mes': resultado_mes,
            'margen_beneficio': margen_beneficio,
            'margen_beneficio_mes': margen_beneficio_mes,
        }
    
    @classmethod
    def get_temporal_data(cls):
        today = timezone.now().date()
        start_date = today.replace(day=1) - timedelta(days=365)
        
        business_payments = cls.get_business_payments_queryset().filter(
            payment_date__gte=start_date
        )
        business_expenses = cls.get_business_expenses_queryset().filter(
            date__gte=start_date
        )
        
        ingresos_por_mes = business_payments.annotate(
            mes=TruncMonth('payment_date')
        ).values('mes').annotate(
            total=cls.get_net_revenue_aggregation()
        ).order_by('mes')
        
        gastos_por_mes = business_expenses.annotate(
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
    def get_business_lines_data(cls, user=None, start_date=None, end_date=None, level=None):
        if user:
            business_line_service = BusinessLineService()
            accessible_lines = business_line_service.get_accessible_lines(user).filter(is_active=True)
        else:
            accessible_lines = BusinessLine.objects.filter(is_active=True)
        
        if level:
            accessible_lines = accessible_lines.filter(level=level)
        
        business_lines = []
        
        for bl in accessible_lines:
            descendant_ids = bl.get_descendant_ids()
            servicios = ClientService.objects.filter(
                business_line__id__in=descendant_ids,
                category=ClientService.CategoryChoices.BUSINESS
            )
            pagos = ServicePayment.objects.filter(client_service__in=servicios)
            
            if start_date:
                pagos = pagos.filter(payment_date__gte=start_date)
            if end_date:
                pagos = pagos.filter(payment_date__lte=end_date)
            
            ingresos_netos = pagos.aggregate(
                total=cls.get_net_revenue_aggregation()
            )['total'] or 0
            
            business_lines.append({
                'name': bl.name,
                'total_ingresos': ingresos_netos,
                'num_servicios': servicios.count(),
            })
        
        business_lines = sorted(business_lines, key=lambda x: x['total_ingresos'], reverse=True)
        total_ingresos = sum(bl['total_ingresos'] for bl in business_lines)
        
        for bl in business_lines:
            bl['porcentaje'] = (bl['total_ingresos'] / total_ingresos * 100) if total_ingresos > 0 else 0
        
        return business_lines
    
    @staticmethod
    def get_expense_categories_data(start_date=None, end_date=None):
        expense_filter = Q(expenses__service_category=Expense.ServiceCategoryChoices.BUSINESS)
        if start_date:
            expense_filter &= Q(expenses__date__gte=start_date)
        if end_date:
            expense_filter &= Q(expenses__date__lte=end_date)
        
        categories = list(ExpenseCategory.objects.annotate(
            total=Sum('expenses__amount', filter=expense_filter),
            count=Count('expenses', filter=expense_filter)
        ).filter(total__isnull=False).order_by('-total'))
        
        total_gastos = sum(cat.total for cat in categories if cat.total)
        
        for cat in categories:
            cat.porcentaje = (cat.total / total_gastos * 100) if total_gastos > 0 and cat.total else 0
        
        return categories
