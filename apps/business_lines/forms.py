from django import forms
from django.core.exceptions import ValidationError
from .models import BusinessLine
from .services.business_line_service import BusinessLineService


class BusinessLineForm(forms.ModelForm):
    """
    Formulario para crear y editar líneas de negocio.
    
    - Para líneas nuevas: no muestra el campo is_active (se crean como inactivas)
    - Para líneas existentes: muestra el estado pero valida que solo se pueda activar si tiene servicios activos
    """
    
    class Meta:
        model = BusinessLine
        fields = ['name', 'parent', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Nombre de la línea de negocio'
            }),
            'parent': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si es una línea nueva (sin pk), ocultar el campo is_active
        if not self.instance.pk:
            self.fields.pop('is_active', None)
        else:
            # Para líneas existentes, añadir ayuda contextual
            self.fields['is_active'].help_text = (
                'Solo se puede activar si la línea tiene servicios activos o sublíneas activas. '
                'El estado se actualiza automáticamente basado en los servicios.'
            )
    
    def clean_is_active(self):
        """
        Valida que una línea solo pueda ser marcada como activa si tiene servicios activos o sublíneas activas.
        """
        is_active = self.cleaned_data.get('is_active', False)
        
        # Si se está intentando activar la línea
        if is_active and self.instance.pk:
            # Verificar si tiene servicios activos o sublíneas activas
            has_active_services = BusinessLineService.check_line_has_active_services(self.instance)
            has_active_sublines = BusinessLineService.check_line_has_active_sublines(self.instance)
            
            if not has_active_services and not has_active_sublines:
                raise ValidationError(
                    'No se puede activar esta línea de negocio porque no tiene servicios activos '
                    'ni sublíneas activas. Primero debe crear servicios activos o activar sublíneas.'
                )
        
        return is_active
    
    def clean_name(self):
        """
        Valida que el nombre sea único dentro del mismo nivel y padre.
        """
        name = self.cleaned_data.get('name')
        parent = self.cleaned_data.get('parent')
        
        if name:
            # Construir el query para verificar unicidad
            queryset = BusinessLine.objects.filter(name__iexact=name, parent=parent)
            
            # Si estamos editando, excluir la instancia actual
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
    """
    Formulario específico para crear líneas de negocio.
    No incluye el campo is_active ya que siempre se crean como inactivas.
    """
    
    class Meta(BusinessLineForm.Meta):
        fields = ['name', 'parent']


class BusinessLineUpdateForm(BusinessLineForm):
    """
    Formulario específico para editar líneas de negocio.
    Incluye el campo is_active con validaciones.
    """
    
    class Meta(BusinessLineForm.Meta):
        fields = ['name', 'parent', 'is_active']
