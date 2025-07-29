from typing import List, Dict, Any
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from . import BaseExporter
from ..services.export_registry import register_exporter


@register_exporter('expense_categories')
class ExpenseCategoryExporter(BaseExporter):
    """Exportador de categorías de gastos con estadísticas"""
    
    def get_data(self) -> List[Dict[str, Any]]:
        try:
            from apps.expenses.models import ExpenseCategory, Expense
            from django_tenants.utils import connection
            
            tenant = connection.tenant
            if not tenant or tenant.schema_name == 'public':
                return []
            
            categories = ExpenseCategory.objects.all()
            data = []
            
            for category in categories:
                # Estadísticas de gastos para esta categoría
                expense_stats = Expense.objects.filter(
                    category=category
                ).aggregate(
                    total_gastos=Count('id'),
                    monto_total=Sum('amount'),
                    monto_promedio=Avg('amount')
                )
                
                category_data = {
                    'id': category.id,
                    'nombre': category.name,
                    'descripcion': category.description or '',
                    'es_activa': category.is_active,
                    'fecha_creacion': category.created.isoformat() if category.created else '',
                    'fecha_modificacion': category.modified.isoformat() if category.modified else '',
                    
                    # Estadísticas
                    'total_gastos': expense_stats['total_gastos'] or 0,
                    'monto_total': float(expense_stats['monto_total'] or 0),
                    'monto_promedio': float(expense_stats['monto_promedio'] or 0),
                }
                data.append(category_data)
            
            return data
            
        except Exception as e:
            print(f"Error exporting expense categories: {e}")
            return []
    
    @classmethod
    def get_display_name(cls) -> str:
        return "Categorías de Gastos"


@register_exporter('expenses')
class ExpenseExporter(BaseExporter):
    """Exportador de gastos individuales"""
    
    def get_data(self) -> List[Dict[str, Any]]:
        try:
            from apps.expenses.models import Expense
            from django_tenants.utils import connection
            
            tenant = connection.tenant
            if not tenant or tenant.schema_name == 'public':
                return []
            
            expenses = Expense.objects.all().select_related('category')
            return self.serialize_queryset(expenses)
            
        except Exception as e:
            print(f"Error exporting expenses: {e}")
            return []
    
    @classmethod
    def get_display_name(cls) -> str:
        return "Gastos"
