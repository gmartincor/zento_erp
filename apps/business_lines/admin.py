from django.contrib import admin
from .models import BusinessLine
from .forms import BusinessLineForm


@admin.register(BusinessLine)
class BusinessLineAdmin(admin.ModelAdmin):
    form = BusinessLineForm
    list_display = ['name', 'slug', 'parent', 'level', 'is_active']
    list_filter = ['level', 'is_active', 'parent']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['level', 'name']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if 'is_active' in form.base_fields:
            form.base_fields['is_active'].help_text = (
                'Una línea de negocio solo puede estar activa si tiene servicios activos '
                'o sublíneas activas. El estado se actualiza automáticamente.'
            )
        
        return form
