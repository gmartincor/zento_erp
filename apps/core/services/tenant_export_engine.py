import uuid
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django_tenants.utils import connection, tenant_context
from .export_registry import ExportRegistry
from .data_serializers import DataSerializerFactory


class TenantDataExporter:
    def __init__(self, tenant=None, format='zip', options=None):
        self.tenant = tenant or connection.tenant
        self.format = format
        self.options = options or {}
        self.export_id = str(uuid.uuid4())
        self.serializer = DataSerializerFactory.get(format)
    
    def export_all(self) -> bytes:
        with tenant_context(self.tenant):
            return self._perform_export()
    
    def _perform_export(self) -> bytes:
        exporters = ExportRegistry.get_tenant_exporters(self.tenant)
        data = {}
        
        for name, exporter_class in exporters.items():
            if self._should_export(name):
                exporter = exporter_class()
                table_data = exporter.get_data()
                if table_data:
                    data[name] = table_data
        
        metadata = self._build_metadata()
        return self.serializer.serialize(data, metadata)
    
    def _should_export(self, exporter_name: str) -> bool:
        if not self.options.get('selected_exporters'):
            return True
        return exporter_name in self.options.get('selected_exporters', [])
    
    def _build_metadata(self) -> Dict[str, Any]:
        return {
            'export_id': self.export_id,
            'tenant_schema': getattr(self.tenant, 'schema_name', 'public'),
            'tenant_name': getattr(self.tenant, 'name', 'Public Schema'),
            'export_date': timezone.now().isoformat(),
            'format': self.format,
            'version': '1.0'
        }
    
    def get_filename(self) -> str:
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        tenant_name = getattr(self.tenant, 'name', 'public_schema')
        tenant_name = tenant_name.replace(' ', '_').lower()
        
        if self.format == 'zip':
            extension = 'zip'
        elif self.format == 'excel':
            extension = 'xlsx'
        else:
            extension = self.format
            
        return f"{tenant_name}_export_{timestamp}.{extension}"


class ExportManager:
    @classmethod
    def create_export(cls, tenant=None, format='zip', options=None) -> TenantDataExporter:
        return TenantDataExporter(tenant=tenant, format=format, options=options)
    
    @classmethod
    def get_available_formats(cls) -> List[str]:
        return DataSerializerFactory.get_available_formats()
    
    @classmethod
    def get_available_exporters(cls, tenant=None) -> Dict[str, str]:
        exporters = ExportRegistry.get_tenant_exporters(tenant)
        return {name: exporter_class.get_display_name() for name, exporter_class in exporters.items()}
