from django import forms
from .models import ExpenseCategory, Expense


class ExpenseCategoryForm(forms.ModelForm):
    """
    Formulario para crear y editar categorías de gastos.
    """
    
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'category_type', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Ej: Internet, Nómina, Seguros Sociales'
            }),
            'category_type': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'rows': 3,
                'placeholder': 'Descripción opcional de la categoría'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].help_text = 'Nombre descriptivo de la categoría (ej: Internet, Nómina, Seguros Sociales)'
        self.fields['category_type'].help_text = 'Tipo de gasto: Fijo (mensual), Variable (ocasional), Impuesto, Puntual'
        self.fields['description'].required = False


class ExpenseForm(forms.ModelForm):
    """
    Formulario para crear y editar gastos.
    """
    
    class Meta:
        model = Expense
        fields = ['description', 'amount', 'date', 'category', 'invoice_number']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Descripción del gasto'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'step': '0.01',
                'min': '0'
            }),
            'date': forms.DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'type': 'date'
            }),
            'category': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'invoice_number': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Número de factura (opcional)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        category_type = kwargs.pop('category_type', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar categorías por tipo si se especifica
        if category_type:
            self.fields['category'].queryset = ExpenseCategory.objects.filter(
                category_type=category_type,
                is_active=True
            ).order_by('name')
        else:
            self.fields['category'].queryset = ExpenseCategory.objects.filter(
                is_active=True
            ).order_by('category_type', 'name')
        
        # Configurar help text
        self.fields['invoice_number'].required = False
        self.fields['invoice_number'].help_text = 'Número de factura o referencia (opcional)'
