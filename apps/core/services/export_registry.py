from typing import Dict, Type, List
from django.apps import apps


class ExportRegistry:
    _exporters: Dict[str, Type] = {}
    _loaded = False
    
    @classmethod
    def _ensure_loaded(cls):
        if not cls._loaded:
            cls._load_exporters()
            cls._loaded = True
    
    @classmethod
    def _load_exporters(cls):
        from ..exporters import accounting
        from ..exporters import business_lines  
        from ..exporters import invoicing
        from ..exporters import expenses
        from ..exporters import tenant
    
    @classmethod
    def register(cls, name: str, exporter_class: Type):
        cls._exporters[name] = exporter_class
    
    @classmethod
    def get_exporters(cls) -> Dict[str, Type]:
        cls._ensure_loaded()
        return cls._exporters.copy()
    
    @classmethod
    def get_exporter(cls, name: str) -> Type:
        cls._ensure_loaded()
        return cls._exporters.get(name)
    
    @classmethod
    def get_tenant_exporters(cls, tenant=None) -> Dict[str, Type]:
        return cls.get_exporters()
    
    @classmethod
    def list_registered(cls) -> List[str]:
        cls._ensure_loaded()
        return list(cls._exporters.keys())


def register_exporter(name: str):
    def decorator(exporter_class: Type):
        ExportRegistry.register(name, exporter_class)
        return exporter_class
    return decorator
