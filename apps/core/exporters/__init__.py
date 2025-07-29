from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
from django.db import models
from django.forms.models import model_to_dict


class BaseExporter(ABC):
    @abstractmethod
    def get_data(self) -> List[Dict[str, Any]]:
        pass
    
    @classmethod
    @abstractmethod
    def get_display_name(cls) -> str:
        pass
    
    def serialize_model_instance(self, instance: models.Model) -> Dict[str, Any]:
        data = model_to_dict(instance)
        
        for field_name, field_value in list(data.items()):
            if hasattr(instance, field_name):
                field_obj = instance._meta.get_field(field_name)
                
                if isinstance(field_obj, models.DateTimeField) and field_value:
                    data[field_name] = field_value.isoformat()
                elif isinstance(field_obj, models.DateField) and field_value:
                    data[field_name] = field_value.isoformat()
                elif isinstance(field_obj, models.DecimalField) and field_value is not None:
                    data[field_name] = str(field_value)
                elif isinstance(field_obj, models.ForeignKey) and field_value:
                    try:
                        related_obj = getattr(instance, field_name)
                        data[field_name] = str(related_obj)
                        data[f"{field_name}_id"] = field_value
                    except:
                        data[field_name] = field_value
        
        return data
    
    def serialize_queryset(self, queryset: Union[models.QuerySet, List[models.Model]]) -> List[Dict[str, Any]]:
        return [self.serialize_model_instance(obj) for obj in queryset]


from . import accounting
from . import business_lines
from . import invoicing
from . import expenses
from . import tenant
