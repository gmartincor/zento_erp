from django.http import HttpResponse
from django.utils import timezone
from datetime import date, datetime, timedelta
from decimal import Decimal
import zipfile
import io
import logging

from .models import Invoice
from .utils import generate_invoice_pdf

logger = logging.getLogger(__name__)


class BulkPDFService:
    @staticmethod
    def get_months_name():
        return [
            (1, 'enero'), (2, 'febrero'), (3, 'marzo'), (4, 'abril'),
            (5, 'mayo'), (6, 'junio'), (7, 'julio'), (8, 'agosto'),
            (9, 'septiembre'), (10, 'octubre'), (11, 'noviembre'), (12, 'diciembre')
        ]
    
    @staticmethod
    def get_period_invoices(period_type, year=None, month=None, quarter=None):
        today = timezone.now().date()
        
        if period_type == 'monthly':
            if year and month:
                start = date(year, month, 1)
                if month == 12:
                    end = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end = date(year, month + 1, 1) - timedelta(days=1)
            else:
                start = today.replace(day=1)
                end = today
        
        elif period_type == 'quarterly':
            if year and quarter:
                start_month = (quarter - 1) * 3 + 1
                start = date(year, start_month, 1)
                if quarter == 4:
                    end = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_month = start_month + 2
                    next_month = end_month + 1
                    if next_month > 12:
                        end = date(year + 1, 1, 1) - timedelta(days=1)
                    else:
                        end = date(year, next_month, 1) - timedelta(days=1)
            else:
                current_quarter = (today.month - 1) // 3 + 1
                start_month = (current_quarter - 1) * 3 + 1
                start = date(today.year, start_month, 1)
                end = today
        
        else:
            raise ValueError(f"Tipo de período no válido: {period_type}")
        
        return Invoice.objects.filter(
            issue_date__range=[start, end],
            status__in=['SENT', 'PAID']
        ).order_by('issue_date', 'reference')
    
    @staticmethod
    def generate_bulk_pdfs_zip(invoices, filename_prefix):
        buffer = io.BytesIO()
        success_count = 0
        error_count = 0
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for invoice in invoices:
                try:
                    pdf_content = generate_invoice_pdf(invoice)
                    pdf_filename = f"{invoice.reference or f'borrador_{invoice.id}'}.pdf"
                    zip_file.writestr(pdf_filename, pdf_content)
                    success_count += 1
                    logger.info(f"PDF added to ZIP: {pdf_filename}")
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error generating PDF for invoice {invoice.id}: {str(e)}")
                    continue
        
        zip_content = buffer.getvalue()
        buffer.close()
        
        if success_count == 0:
            logger.warning("No PDFs generated for ZIP file")
            return None, 0, error_count
        
        return zip_content, success_count, error_count
    
    @staticmethod
    def create_zip_response(zip_content, filename):
        response = HttpResponse(zip_content, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    @staticmethod
    def get_period_summary(invoices):
        if not invoices:
            return {
                'count': 0,
                'total_amount': Decimal('0.00'),
                'date_range': 'Sin facturas'
            }
        
        total_amount = sum(invoice.total_amount for invoice in invoices)
        start_date = invoices.first().issue_date
        end_date = invoices.last().issue_date
        
        return {
            'count': invoices.count(),
            'total_amount': total_amount,
            'date_range': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        }
    
    @staticmethod
    def get_months_name():
        return [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ]
    
    @staticmethod
    def get_quarters_name():
        return [
            (1, 'Q1 (Enero - Marzo)'), (2, 'Q2 (Abril - Junio)'),
            (3, 'Q3 (Julio - Septiembre)'), (4, 'Q4 (Octubre - Diciembre)')
        ]
