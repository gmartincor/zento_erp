from typing import List, Dict, Any
from ..services.export_registry import register_exporter
from . import BaseExporter


from .base import BaseExporter
from ..services.export_registry import register_exporter


@register_exporter('companies')
class CompanyExporter(BaseExporter):
    
    def get_data(self):
        try:
            from apps.invoicing.models import Company
            
            companies = Company.objects.all().order_by('-created')
            
            if not companies.exists():
                return [{
                    'mensaje': 'No hay información de empresa configurada',
                    'recomendacion': 'Configure los datos de su empresa en el módulo de facturación'
                }]
            
            data = []
            for company in companies:
                company_data = {
                    'forma_legal': company.get_legal_form_display() if company.legal_form else '',
                    'nombre_comercial': company.business_name or '',
                    'razon_social': company.legal_name or '',
                    'nif_cif': company.tax_id or '',
                    'direccion_completa': f"{company.address or ''}, {company.postal_code or ''} {company.city or ''}, {company.province or ''}".strip(', '),
                    'telefono': company.phone or '',
                    'email': company.email or '',
                    'banco': company.bank_name or '',
                    'iban': company.iban or '',
                    'registro_mercantil': company.mercantile_registry or '',
                    'capital_social': float(company.share_capital) if company.share_capital else 0.0,
                    'prefijo_factura': company.invoice_prefix or '',
                    'numero_actual_factura': company.current_number or 0,
                    'tiene_logo': 'Sí' if company.logo else 'No',
                    'fecha_creacion': company.created.strftime('%Y-%m-%d %H:%M') if hasattr(company, 'created') else '',
                }
                data.append(company_data)
            
            return data
            
        except Exception as e:
            print(f"Error exporting companies: {e}")
            return []


@register_exporter('invoices')
class InvoiceExporter(BaseExporter):
    """Exportador profesional de facturas"""
    
    def get_data(self):
        try:
            from apps.invoicing.models import Invoice
            
            invoices = Invoice.objects.select_related('company').prefetch_related(
                'items'
            ).order_by('-issue_date', '-id')
            
            if not invoices.exists():
                return [{
                    'mensaje': 'No hay facturas emitidas',
                    'recomendacion': 'Las facturas aparecerán aquí cuando empiece a facturar'
                }]
            
            data = []
            for invoice in invoices:
                invoice_data = {
                    'referencia': invoice.reference or '',
                    'fecha_emision': invoice.issue_date.strftime('%Y-%m-%d'),
                    'cliente_nombre': invoice.client_name or '',
                    'cliente_nif': invoice.client_tax_id or '',
                    'cliente_direccion': invoice.client_address or '',  
                    'tipo_cliente': invoice.get_client_type_display() if hasattr(invoice, 'get_client_type_display') else '',
                    'condiciones_pago': invoice.payment_terms or '',
                    'estado': invoice.get_status_display() if hasattr(invoice, 'get_status_display') else 'Emitida',
                    'numero_items': invoice.items.count() if hasattr(invoice, 'items') else 0,
                    'empresa_emisora': invoice.company.business_name if invoice.company else '',
                    'tiene_pdf': 'Sí' if getattr(invoice, 'pdf_file', None) else 'No',
                    'fecha_creacion': invoice.created.strftime('%Y-%m-%d %H:%M') if hasattr(invoice, 'created') else '',
                }
                data.append(invoice_data)
            
            return data
            
        except Exception as e:
            print(f"Error exporting invoices: {e}")
            return []


@register_exporter('invoice_items')
class InvoiceItemExporter(BaseExporter):
    
    def get_data(self):
        try:
            from apps.invoicing.models import InvoiceItem
            
            items = InvoiceItem.objects.select_related('invoice').order_by(
                '-invoice__issue_date', 'invoice__id', 'id'
            )
            
            if not items.exists():
                return [{
                    'mensaje': 'No hay conceptos de factura',
                    'recomendacion': 'Los conceptos de factura aparecerán cuando empiece a facturar servicios'
                }]
            
            data = []
            for item in items:
                item_data = {
                    'factura_referencia': item.invoice.reference if item.invoice.reference else f'ID-{item.invoice.id}',
                    'factura_fecha': item.invoice.issue_date.strftime('%Y-%m-%d'),
                    'concepto_descripcion': item.description or '',
                    'cantidad': float(item.quantity) if item.quantity else 0.0,
                    'precio_unitario': float(item.unit_price) if item.unit_price else 0.0,
                    'subtotal_concepto': float(item.quantity * item.unit_price) if item.quantity and item.unit_price else 0.0,
                    'cliente_factura': item.invoice.client_name if item.invoice.client_name else '',
                    'fecha_creacion': item.created.strftime('%Y-%m-%d %H:%M') if hasattr(item, 'created') else '',
                }
                data.append(item_data)
            
            return data
            
        except Exception as e:
            print(f"Error exporting invoice items: {e}")
            return []
