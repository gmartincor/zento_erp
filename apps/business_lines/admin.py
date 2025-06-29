from django.contrib import admin
from .models import BusinessLine


@admin.register(BusinessLine)
class BusinessLineAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'level', 'is_active']
    list_filter = ['level', 'is_active', 'parent']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['level', 'name']
