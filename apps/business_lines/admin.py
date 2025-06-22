from django.contrib import admin
from django.utils.html import format_html
from .models import BusinessLine


@admin.register(BusinessLine)
class BusinessLineAdmin(admin.ModelAdmin):
    """
    Admin interface for BusinessLine with hierarchical display.
    """
    
    list_display = [
        'hierarchical_name_display',
        'level',
        'has_remanente',
        'remanente_field',
        'is_active',
        'order',
        'created'
    ]
    
    list_filter = [
        'level',
        'is_active',
        'has_remanente',
        'remanente_field'
    ]
    
    search_fields = ['name', 'slug']
    
    list_editable = ['is_active', 'order']
    
    ordering = ['level', 'order', 'name']
    
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'slug', 'parent')
        }),
        ('Configuración', {
            'fields': ('is_active', 'order')
        }),
        ('Remanente', {
            'fields': ('has_remanente', 'remanente_field'),
            'classes': ('collapse',)
        }),
        ('Información del sistema', {
            'fields': ('level', 'created', 'modified'),
            'classes': ('collapse',),
            'description': 'Campos calculados automáticamente'
        })
    )
    
    readonly_fields = ['level', 'created', 'modified']

    def get_queryset(self, request):
        """
        Optimize queries with select_related for parent relationships.
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('parent')

    def hierarchical_name_display(self, obj):
        """
        Display name with hierarchical indentation based on level.
        """
        indent = '&nbsp;&nbsp;&nbsp;&nbsp;' * (obj.level - 1)
        level_indicator = '└─ ' if obj.level > 1 else ''
        
        # Add visual indicators for active/inactive status
        status_icon = '✓' if obj.is_active else '✗'
        status_color = 'green' if obj.is_active else 'red'
        
        return format_html(
            '{}<span style="color: {};">{}</span> {}{}',
            indent,
            status_color,
            status_icon,
            level_indicator,
            obj.name
        )
    
    hierarchical_name_display.short_description = 'Nombre (Jerarquía)'
    hierarchical_name_display.admin_order_field = 'name'

    def get_form(self, request, obj=None, **kwargs):
        """
        Customize form based on object context.
        """
        form = super().get_form(request, obj, **kwargs)
        
        # Limit parent choices to avoid circular references
        if obj:
            # Exclude self and descendants from parent choices
            excluded_ids = list(obj.get_descendant_ids())
            form.base_fields['parent'].queryset = BusinessLine.objects.exclude(
                id__in=excluded_ids
            ).filter(level__lt=3)  # Can't be parent if already at level 3
        else:
            # For new objects, only allow levels 1 and 2 as parents
            form.base_fields['parent'].queryset = BusinessLine.objects.filter(level__lt=3)
        
        return form

    def save_model(self, request, obj, form, change):
        """
        Custom save to handle remanente field validation.
        """
        # Clear remanente_field if has_remanente is False
        if not obj.has_remanente:
            obj.remanente_field = None
        
        super().save_model(request, obj, form, change)
