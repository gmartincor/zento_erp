from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from .models import Company, Invoice, InvoiceItem

FORM_CONTROL_CLASS = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        exclude = ['current_number']
        widgets = {
            'legal_form': forms.Select(attrs={'class': FORM_CONTROL_CLASS}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': FORM_CONTROL_CLASS}),
            'business_name': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'legal_name': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'tax_id': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'postal_code': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'city': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'province': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'phone': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'email': forms.EmailInput(attrs={'class': FORM_CONTROL_CLASS}),
            'bank_name': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'iban': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'mercantile_registry': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'share_capital': forms.NumberInput(attrs={'step': '0.01', 'class': FORM_CONTROL_CLASS}),
            'invoice_prefix': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'logo': forms.ClearableFileInput(attrs={'class': FORM_CONTROL_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['legal_form'].required = True
        
        self.fields['invoice_prefix'].help_text = 'Prefijo para numeración de facturas (ej: FN, FACT)'
        self.fields['share_capital'].help_text = 'Opcional en facturas, pero obligatorio en correspondencia comercial para SL/SA'
        self.fields['mercantile_registry'].help_text = 'Opcional en facturas, pero recomendable para transparencia'


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['client_type', 'client_name', 'client_tax_id', 'client_address', 'issue_date', 'payment_terms', 'status']
        widgets = {
            'client_type': forms.Select(attrs={'class': FORM_CONTROL_CLASS}),
            'client_name': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'client_tax_id': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'client_address': forms.Textarea(attrs={'rows': 3, 'class': FORM_CONTROL_CLASS}),
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': FORM_CONTROL_CLASS}),
            'payment_terms': forms.Textarea(attrs={'rows': 2, 'class': FORM_CONTROL_CLASS}),
            'status': forms.Select(attrs={'class': FORM_CONTROL_CLASS}),
        }

    def clean_client_tax_id(self):
        client_type = self.cleaned_data.get('client_type')
        client_tax_id = self.cleaned_data.get('client_tax_id')
        
        if client_type == 'COMPANY' and not client_tax_id:
            raise ValidationError("El CIF es obligatorio para empresas.")
        
        return client_tax_id


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price', 'vat_rate', 'irpf_rate']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 2, 
                'class': FORM_CONTROL_CLASS,
                'placeholder': 'Descripción del servicio o producto'
            }),
            'quantity': forms.NumberInput(attrs={'class': FORM_CONTROL_CLASS, 'min': '1', 'value': '1'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'class': FORM_CONTROL_CLASS, 'min': '0.01'}),
            'vat_rate': forms.NumberInput(attrs={'step': '0.01', 'class': FORM_CONTROL_CLASS, 'min': '0', 'max': '100'}),
            'irpf_rate': forms.NumberInput(attrs={'step': '0.01', 'class': FORM_CONTROL_CLASS, 'min': '0', 'max': '100'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        self.fields['irpf_rate'].required = False
    
    def has_changed(self):
        return bool(self.data.get(self.add_prefix('description')))

class BaseInvoiceItemFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance or not self.instance.pk or not self.instance.items.exists():
            self.extra = 1
        else:
            self.extra = 0
    
    def clean(self):
        if any(self.errors):
            return
        
        valid_forms = 0
        for form in self.forms:
            if form.cleaned_data.get('DELETE', False):
                continue
            if form.cleaned_data.get('description'):
                valid_forms += 1
        
        if valid_forms < 1:
            raise forms.ValidationError('Debe añadir al menos un producto o servicio.')

InvoiceItemFormSet = inlineformset_factory(
    Invoice, 
    InvoiceItem,
    form=InvoiceItemForm,
    formset=BaseInvoiceItemFormSet,
    fields=['description', 'quantity', 'unit_price', 'vat_rate', 'irpf_rate'],
    extra=0,
    min_num=0,
    validate_min=False,
    can_delete=True,
    max_num=50
)
