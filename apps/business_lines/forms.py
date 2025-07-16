from django import forms
from django.core.exceptions import ValidationError
from .models import BusinessLine
from .services.business_line_service import BusinessLineService


class BusinessLineForm(forms.ModelForm):
    class Meta:
        model = BusinessLine
        fields = ['name', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Nombre de la línea de negocio'
            }),
            'parent': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-primary-500 focus:ring-primary-500'
            })
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        parent = self.cleaned_data.get('parent')
        
        if name:
            queryset = BusinessLine.objects.filter(name__iexact=name, parent=parent)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                if parent:
                    raise ValidationError(
                        f'Ya existe una línea de negocio con el nombre "{name}" bajo el padre "{parent.name}".'
                    )
                else:
                    raise ValidationError(
                        f'Ya existe una línea de negocio raíz con el nombre "{name}".'
                    )
        
        return name


class BusinessLineCreateForm(BusinessLineForm):
    class Meta(BusinessLineForm.Meta):
        fields = ['name', 'parent']


class BusinessLineUpdateForm(BusinessLineForm):
    class Meta(BusinessLineForm.Meta):
        fields = ['name', 'parent']
