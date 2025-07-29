from django.shortcuts import redirect, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse, Http404, JsonResponse
from django.db.models import Q
from django.db import transaction
from datetime import datetime, date, timedelta
from django.utils import timezone
import logging

from .models import Company, Invoice, InvoiceItem
from .forms import CompanyForm, InvoiceForm, InvoiceItemFormSet
from .utils import generate_invoice_pdf
from .services import BulkPDFService
from apps.core.services.temporal_service import get_available_years

logger = logging.getLogger(__name__)

class CompanyMixin:
    def get_company(self):
        try:
            return Company.objects.get()
        except Company.DoesNotExist:
            messages.error(
                self.request, 
                'Debe configurar los datos de la empresa antes de crear facturas.'
            )
            logger.warning("Attempted to access invoicing without company configuration")
            return None
        except Company.MultipleObjectsReturned:
            logger.error("Multiple companies found for tenant")
            return Company.objects.first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.get_company()
        return context

class CompanyFormMixin:
    def form_valid(self, form):
        response = super().form_valid(form)
        action = 'creada' if not self.object.pk else 'actualizada'
        messages.success(self.request, f'Configuración de empresa {action} correctamente.')
        logger.info(f"Company configuration {action}: {form.instance.business_name}")
        return response

class CompanyCreateView(CompanyFormMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'invoicing/company_form.html'
    success_url = reverse_lazy('invoicing:invoice_list')
    
    def get(self, request, *args, **kwargs):
        if Company.objects.exists():
            return redirect('invoicing:company_edit')
        return super().get(request, *args, **kwargs)

class CompanyUpdateView(CompanyFormMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'invoicing/company_form.html'
    success_url = reverse_lazy('invoicing:invoice_list')
    
    def get_object(self):
        try:
            return Company.objects.get()
        except Company.DoesNotExist:
            raise Http404("No existe configuración de empresa.")
            
    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            messages.error(request, 'No existe configuración de empresa.')
            return redirect('invoicing:company_create')
        return super().get(request, *args, **kwargs)

class InvoiceListView(ListView):
    model = Invoice
    template_name = 'invoicing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    ordering = ['-issue_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        period = self.request.GET.get('period', 'current_month')
        
        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search) |
                Q(client_name__icontains=search) |
                Q(client_tax_id__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
            
        queryset = self._apply_period_filter(queryset, period)
        
        return queryset

    def _apply_period_filter(self, queryset, period_type):
        today = timezone.now().date()
        
        if period_type == 'current_month':
            start = today.replace(day=1)
            end = today
        elif period_type == 'last_month':
            last_month = today.replace(day=1) - timedelta(days=1)
            start = last_month.replace(day=1)
            end = last_month
        elif period_type == 'current_year':
            start = today.replace(month=1, day=1)
            end = today
        elif period_type == 'last_year':
            last_year = today.year - 1
            start = date(last_year, 1, 1)
            end = date(last_year, 12, 31)
        elif period_type == 'last_3_months':
            start = today - timedelta(days=90)
            end = today
        elif period_type == 'last_6_months':
            start = today - timedelta(days=180)
            end = today
        elif period_type == 'last_12_months':
            start = today - timedelta(days=365)
            end = today
        elif period_type == 'all_time':
            return queryset
        else:
            return queryset
            
        return queryset.filter(issue_date__range=[start, end])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        context['period'] = self.request.GET.get('period', 'current_month')
        context['has_company'] = Company.objects.exists()
        context['current_year'] = timezone.now().year
        context['available_years'] = get_available_years()
        
        context['available_periods'] = [
            ('current_month', 'Mes actual'),
            ('last_month', 'Mes anterior'),
            ('current_year', 'Año actual'),
            ('last_year', 'Año anterior'),
            ('last_3_months', 'Últimos 3 meses'),
            ('last_6_months', 'Últimos 6 meses'),
            ('last_12_months', 'Últimos 12 meses'),
            ('all_time', 'Histórico total'),
        ]
        
        return context

class InvoiceDetailView(DetailView):
    model = Invoice
    template_name = 'invoicing/invoice_detail.html'
    context_object_name = 'invoice'

class InvoiceCreateView(CompanyMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoicing/invoice_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.get_company():
            return redirect('invoicing:company_create')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.get_company()
        
        if self.request.POST:
            context['formset'] = InvoiceItemFormSet(
                self.request.POST, 
                instance=self.object,
                form_kwargs={'company': self.get_company()}
            )
        else:
            context['formset'] = InvoiceItemFormSet(
                instance=self.object,
                form_kwargs={'company': self.get_company()}
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            with transaction.atomic():
                form.instance.company = self.get_company()
                self.object = form.save()
                formset.instance = self.object
                formset.save()
                
                logger.info(f"Invoice created: {self.object.reference or 'DRAFT'} for {self.object.client_name}")
                messages.success(
                    self.request, 
                    f'Factura {self.object.reference or "borrador"} creada correctamente.'
                )
                return redirect(self.get_success_url())
        
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('invoicing:invoice_detail', kwargs={'pk': self.object.pk})

class InvoiceUpdateView(UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoicing/invoice_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.object.company
        context['is_edit'] = True
        
        if self.request.POST:
            context['formset'] = InvoiceItemFormSet(
                self.request.POST, 
                instance=self.object,
                form_kwargs={'company': self.object.company}
            )
        else:
            context['formset'] = InvoiceItemFormSet(
                instance=self.object,
                form_kwargs={'company': self.object.company}
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        with transaction.atomic():
            old_status = self.object.status if self.object else None
            self.object = form.save()
            
            if formset.is_valid():
                formset.save()
                
                if old_status == 'DRAFT' and self.object.status != 'DRAFT':
                    self.object.assign_reference_if_needed()
                    self.object.save(update_fields=['reference'])
                
                logger.info(f"Invoice updated: {self.object.reference or 'DRAFT'} for {self.object.client_name}")
                messages.success(
                    self.request, 
                    f'Factura {self.object.reference or "borrador"} actualizada correctamente.'
                )
                return redirect(self.get_success_url())
            else:
                return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('invoicing:invoice_detail', kwargs={'pk': self.object.pk})

def generate_pdf_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    try:
        pdf_content = generate_invoice_pdf(invoice)
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = f'factura_{invoice.reference or "borrador"}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"PDF generated for invoice: {invoice.reference or 'DRAFT'}")
        return response
    except Exception as e:
        logger.error(f"Error generating PDF for invoice {invoice.reference or 'DRAFT'}: {str(e)}")
        messages.error(request, f'Error al generar el PDF: {str(e)}')
        return redirect('invoicing:invoice_detail', pk=pk)


def bulk_download_monthly_view(request):
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    status = request.GET.get('status', None)
    
    try:
        invoices = BulkPDFService.get_period_invoices('monthly', year=year, month=month, status=status)
        
        if not invoices.exists():
            status_text = ""
            if status == 'SENT':
                status_text = " enviadas"
            elif status == 'PAID':
                status_text = " pagadas"
            else:
                status_text = " enviadas o pagadas"
            messages.warning(request, f'No se encontraron facturas{status_text} para {month:02d}/{year}')
            return redirect('invoicing:invoice_list')
        
        zip_content, success_count, error_count = BulkPDFService.generate_bulk_pdfs_zip(
            invoices, 
            f"facturas_{year}_{month:02d}"
        )
        
        if not zip_content:
            messages.error(request, 'Error al generar el archivo ZIP')
            return redirect('invoicing:invoice_list')
        
        month_names = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        
        filename = f"facturas_{month_names[month]}_{year}.zip"
        
        if error_count > 0:
            messages.warning(
                request, 
                f'Descarga completada: {success_count} facturas generadas, {error_count} errores'
            )
        else:
            messages.success(
                request, 
                f'Descarga completada: {success_count} facturas de {month_names[month]} {year}'
            )
        
        logger.info(f"Bulk monthly download: {success_count} invoices for {month:02d}/{year}")
        
        return BulkPDFService.create_zip_response(zip_content, filename)
        
    except Exception as e:
        logger.error(f"Error in bulk monthly download: {str(e)}")
        messages.error(request, f'Error al generar la descarga masiva: {str(e)}')
        return redirect('invoicing:invoice_list')


def bulk_download_quarterly_view(request):
    year = int(request.GET.get('year', timezone.now().year))
    quarter = int(request.GET.get('quarter', (timezone.now().month - 1) // 3 + 1))
    status = request.GET.get('status', None)
    
    try:
        invoices = BulkPDFService.get_period_invoices('quarterly', year=year, quarter=quarter, status=status)
        
        if not invoices.exists():
            status_text = ""
            if status == 'SENT':
                status_text = " enviadas"
            elif status == 'PAID':
                status_text = " pagadas"
            else:
                status_text = " enviadas o pagadas"
            messages.warning(request, f'No se encontraron facturas{status_text} para Q{quarter}/{year}')
            return redirect('invoicing:invoice_list')
        
        zip_content, success_count, error_count = BulkPDFService.generate_bulk_pdfs_zip(
            invoices, 
            f"facturas_{year}_Q{quarter}"
        )
        
        if not zip_content:
            messages.error(request, 'Error al generar el archivo ZIP')
            return redirect('invoicing:invoice_list')
        
        filename = f"facturas_Q{quarter}_{year}.zip"
        
        if error_count > 0:
            messages.warning(
                request, 
                f'Descarga completada: {success_count} facturas generadas, {error_count} errores'
            )
        else:
            messages.success(
                request, 
                f'Descarga completada: {success_count} facturas del Q{quarter} {year}'
            )
        
        logger.info(f"Bulk quarterly download: {success_count} invoices for Q{quarter}/{year}")
        
        return BulkPDFService.create_zip_response(zip_content, filename)
        
    except Exception as e:
        logger.error(f"Error in bulk quarterly download: {str(e)}")
        messages.error(request, f'Error al generar la descarga masiva: {str(e)}')
        return redirect('invoicing:invoice_list')


def bulk_preview_view(request):
    period_type = request.GET.get('type')
    year = int(request.GET.get('year', timezone.now().year))
    status = request.GET.get('status', None)
    
    try:
        if period_type == 'monthly':
            month = int(request.GET.get('month', timezone.now().month))
            invoices = BulkPDFService.get_period_invoices('monthly', year=year, month=month, status=status)
            period_name = f"{BulkPDFService.get_months_name()[month-1][1]} {year}"
        elif period_type == 'quarterly':
            quarter = int(request.GET.get('quarter', (timezone.now().month - 1) // 3 + 1))
            invoices = BulkPDFService.get_period_invoices('quarterly', year=year, quarter=quarter, status=status)
            period_name = f"Q{quarter} {year}"
        else:
            return JsonResponse({'error': 'Tipo de período no válido'}, status=400)
        
        summary = BulkPDFService.get_period_summary(invoices)
        
        return JsonResponse({
            'count': summary['count'],
            'total_amount': summary['total_amount'],
            'date_range': summary['date_range'],
            'period_name': period_name,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error in bulk preview: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
