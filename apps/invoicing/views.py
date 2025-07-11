from django.shortcuts import redirect, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse, Http404
from django.db.models import Q
from django.db import transaction
import logging

from .models import Company, Invoice, InvoiceItem
from .forms import CompanyForm, InvoiceForm, InvoiceItemFormSet
from .utils import generate_invoice_pdf

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
        
        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search) |
                Q(client_name__icontains=search) |
                Q(client_tax_id__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        context['has_company'] = Company.objects.exists()
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
                
                logger.info(f"Invoice created: {self.object.reference} for {self.object.client_name}")
                messages.success(
                    self.request, 
                    f'Factura {self.object.reference} creada correctamente.'
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
            self.object = form.save()
            
            if formset.is_valid():
                formset.save()
                
                logger.info(f"Invoice updated: {self.object.reference} for {self.object.client_name}")
                messages.success(
                    self.request, 
                    f'Factura {self.object.reference} actualizada correctamente.'
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
        filename = f'factura_{invoice.reference}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"PDF generated for invoice: {invoice.reference}")
        return response
    except Exception as e:
        logger.error(f"Error generating PDF for invoice {invoice.reference}: {str(e)}")
        messages.error(request, f'Error al generar el PDF: {str(e)}')
        return redirect('invoicing:invoice_detail', pk=pk)
