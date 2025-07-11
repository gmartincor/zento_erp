from django import forms
from django.core.exceptions import ValidationError
from .models import Company, Invoice, VATRate, IRPFRate

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
            'default_vat_rate': forms.NumberInput(attrs={'step': '0.01', 'class': FORM_CONTROL_CLASS}),
            'irpf_rate': forms.NumberInput(attrs={'step': '0.01', 'class': FORM_CONTROL_CLASS}),
            'invoice_prefix': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'logo': forms.ClearableFileInput(attrs={'class': FORM_CONTROL_CLASS}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Legal form es obligatorio
        self.fields['legal_form'].required = True
        
        # Ayudas contextuales
        self.fields['invoice_prefix'].help_text = 'Prefijo para numeración de facturas (ej: FN, FACT)'
        self.fields['irpf_rate'].help_text = 'Solo se aplica a autónomos que facturen a empresas por importes > 300€'
        self.fields['share_capital'].help_text = 'Opcional en facturas, pero obligatorio en correspondencia comercial para SL/SA'
        self.fields['mercantile_registry'].help_text = 'Opcional en facturas, pero recomendable para transparencia'


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'client_type', 'client_name', 'client_tax_id', 'client_address',
            'issue_date', 'service_description', 'quantity', 'unit_price',
            'vat_rate', 'irpf_rate', 'payment_terms'
        ]
        widgets = {
            'client_type': forms.Select(attrs={'class': FORM_CONTROL_CLASS}),
            'client_name': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'client_tax_id': forms.TextInput(attrs={'class': FORM_CONTROL_CLASS}),
            'client_address': forms.Textarea(attrs={'rows': 3, 'class': FORM_CONTROL_CLASS}),
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': FORM_CONTROL_CLASS}),
            'service_description': forms.Textarea(attrs={
                'rows': 6, 
                'class': FORM_CONTROL_CLASS,
                'placeholder': 'Descripción del servicio. Puede usar viñetas:\n• Servicio 1\n• Servicio 2\n• Servicio 3'
            }),
            'quantity': forms.NumberInput(attrs={'class': FORM_CONTROL_CLASS, 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'class': FORM_CONTROL_CLASS, 'min': '0.01'}),
            'vat_rate': forms.Select(attrs={'class': FORM_CONTROL_CLASS}),
            'irpf_rate': forms.Select(attrs={'class': FORM_CONTROL_CLASS}),
            'payment_terms': forms.Textarea(attrs={'rows': 2, 'class': FORM_CONTROL_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vat_rate'].queryset = VATRate.objects.all()
        self.fields['irpf_rate'].queryset = IRPFRate.objects.all()
        self.fields['irpf_rate'].required = False
        self.fields['irpf_rate'].empty_label = "Sin retención"
        
        try:
            default_vat = VATRate.objects.filter(is_default=True).first()
            if default_vat:
                self.fields['vat_rate'].initial = default_vat
        except VATRate.DoesNotExist:
            pass
            
        try:
            default_irpf = IRPFRate.objects.filter(is_default=True).first()
            if default_irpf:
                self.fields['irpf_rate'].initial = default_irpf
        except IRPFRate.DoesNotExist:
            pass

    def clean_client_tax_id(self):
        client_type = self.cleaned_data.get('client_type')
        client_tax_id = self.cleaned_data.get('client_tax_id')
        
        if client_type == 'COMPANY' and not client_tax_id:
            raise ValidationError("El CIF es obligatorio para empresas.")
        
        return client_tax_id
