from django import forms
from datetime import date
from django.utils import timezone

from ..models import ClientService
from ..services.service_manager import ServiceManager


class ServiceDateEditForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            self._setup_date_fields()
    
    def _setup_date_fields(self):
        restrictions = ServiceManager.get_date_edit_restrictions(self.instance)
        if not restrictions.can_edit_dates:
            self._disable_date_fields(restrictions.restriction_reason)
        else:
            self._setup_editable_date_fields()
    
    def _disable_date_fields(self, reason: str):
        if 'start_date' in self.fields:
            self.fields['start_date'].disabled = True
            self.fields['start_date'].help_text = reason
    
    def _setup_editable_date_fields(self):
        if 'start_date' in self.fields:
            self.fields['start_date'].help_text = "Fecha de inicio del servicio"
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.instance and self.instance.pk:
            start_date = cleaned_data.get('start_date')
            
            restrictions = ServiceManager.get_date_edit_restrictions(self.instance)
            if not restrictions.can_edit_dates:
                if start_date != self.instance.start_date:
                    raise forms.ValidationError(restrictions.restriction_reason)
        
        return cleaned_data
    
    class Meta:
        model = ClientService
        fields = ['start_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
