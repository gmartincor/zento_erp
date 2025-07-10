from django import forms
from django.forms import inlineformset_factory
from .models import Company, Invoice, InvoiceLine

FORM_CONTROL_CLASS = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'
        widgets = {
            'entity_type': forms.RadioSelect(),
            'address': forms.Textarea(attrs={'rows': 3, 'class': FORM_CONTROL_CLASS}),
            'business_name': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'legal_name': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'tax_id': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'postal_code': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'city': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'phone': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'email': forms.EmailInput(attrs={'class': FORM_CONTROL_CLASS}),
            'bank_name': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'iban': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'default_vat_rate': forms.NumberInput(attrs={'step': '0.01', 'class': FORM_CONTROL_CLASS}),
            'irpf_rate': forms.NumberInput(attrs={'step': '0.01', 'class': FORM_CONTROL_CLASS}),
            'invoice_prefix': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'current_number': forms.NumberInput(attrs={'class': FORM_CONTROL_CLASS}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['client_type', 'client_name', 'client_tax_id', 'client_address', 'issue_date', 'payment_terms']
        widgets = {
            'client_type': forms.RadioSelect(),
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': FORM_CONTROL_CLASS}),
            'client_address': forms.Textarea(attrs={'rows': 3, 'class': FORM_CONTROL_CLASS}),
            'client_name': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'client_tax_id': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'payment_terms': forms.Textarea(attrs={'rows': 2, 'class': FORM_CONTROL_CLASS}),
        }


class InvoiceLineForm(forms.ModelForm):
    class Meta:
        model = InvoiceLine
        fields = ['description', 'quantity', 'unit_price', 'vat_rate']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': FORM_CONTROL_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': FORM_CONTROL_CLASS}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'class': FORM_CONTROL_CLASS}),
            'vat_rate': forms.Select(choices=[
                (0, '0% - Exento'),
                (4, '4% - Tipo reducido'),
                (10, '10% - Tipo reducido'),
                (21, '21% - Tipo general'),
            ], attrs={'class': FORM_CONTROL_CLASS}),
        }


InvoiceLineFormSet = inlineformset_factory(
    Invoice, InvoiceLine, form=InvoiceLineForm, extra=1, can_delete=True
)
