from django.shortcuts import redirect, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse
from .models import Company, Invoice, InvoiceLine
from .forms import CompanyForm, InvoiceForm, InvoiceLineFormSet
from .utils import generate_invoice_pdf


class CompanyCreateView(CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'invoicing/company_form.html'
    success_url = reverse_lazy('invoicing:invoice_list')

    def form_valid(self, form):
        messages.success(self.request, 'Configuración de empresa guardada correctamente.')
        return super().form_valid(form)


class InvoiceListView(ListView):
    model = Invoice
    template_name = 'invoicing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    ordering = ['-issue_date']


class InvoiceDetailView(DetailView):
    model = Invoice
    template_name = 'invoicing/invoice_detail.html'
    context_object_name = 'invoice'


class InvoiceCreateView(CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoicing/invoice_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['formset'] = InvoiceLineFormSet(self.request.POST)
        else:
            context['formset'] = InvoiceLineFormSet()
        
        company = Company.objects.first()
        if not company:
            company = Company.objects.create(
                entity_type='COMPANY',
                business_name='Mi Empresa',
                legal_name='Mi Empresa S.L.',
                tax_id='12345678A',
                address='Calle Principal 123',
                postal_code='28001',
                city='Madrid',
                bank_name='Banco Ejemplo',
                iban='ES1234567890123456789012',
            )
        
        context['company'] = company
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            company = context['company']
            form.instance.company = company
            
            # Save the invoice first
            self.object = form.save()
            
            # Generate the reference now that we have the saved object
            if not self.object.reference:
                self.object.reference = self.object.generate_reference()
                self.object.save()
            
            # Save the formset
            formset.instance = self.object
            formset.save()
            
            messages.success(self.request, f'Factura {self.object.reference} creada correctamente.')
            return redirect('invoicing:invoice_detail', pk=self.object.pk)
        else:
            return self.form_invalid(form)


def generate_pdf_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    pdf_content = generate_invoice_pdf(invoice)
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{invoice.reference}.pdf"'
    return response
