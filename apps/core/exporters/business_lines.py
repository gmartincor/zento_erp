from typing import List, Dict, Any
from .base import BaseExporter
from ..services.export_registry import register_exporter


@register_exporter('business_lines')
class BusinessLineExporter(BaseExporter):
    
    def get_data(self):
        try:
            from apps.business_lines.models import BusinessLine
            
            lines = BusinessLine.objects.prefetch_related(
                'client_services__client',
                'client_services__payments',
                'children'
            ).order_by('level', 'order', 'name')
            
            if not lines.exists():
                return []
            
            data = []
            for line in lines:
                # Información básica de la línea
                line_data = {
                    'nombre': line.name,
                    'nivel': line.level,
                    'padre': line.parent.name if line.parent else 'Línea raíz',
                    'ruta_completa': self._get_full_path(line),
                    'orden': line.order,
                    'activa': 'Sí' if line.is_active else 'No',
                    'fecha_creacion': line.created.strftime('%Y-%m-%d'),
                }
                
                # Estadísticas de servicios
                services = line.client_services.filter(is_active=True)
                total_servicios = services.count()
                clientes_unicos = services.values('client').distinct().count()
                
                # Estadísticas financieras
                total_ingresos = sum(s.price for s in services)
                pagos_realizados = 0
                ingresos_reales = 0
                
                for service in services:
                    pagos = service.payments.filter(status='PAID')
                    pagos_realizados += pagos.count()
                    ingresos_reales += sum(p.amount for p in pagos if p.amount)
                
                line_data.update({
                    'total_servicios': total_servicios,
                    'clientes_unicos': clientes_unicos,
                    'ingresos_estimados': float(total_ingresos),
                    'ingresos_reales': float(ingresos_reales),
                    'pagos_realizados': pagos_realizados,
                    'tiene_sublíneas': line.children.exists(),
                    'numero_sublíneas': line.children.count(),
                })
                
                data.append(line_data)
            
            return data
            
        except Exception as e:
            print(f"Error exporting business lines: {e}")
            return []
    
    def _get_full_path(self, line):
        path = [line.name]
        current = line.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' > '.join(path)
