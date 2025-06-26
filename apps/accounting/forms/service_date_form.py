from django import forms
from datetime import date
from django.utils import timezone

from ..models import ClientService
from ..services.service_date_manager import ServiceDateManager


class ServiceDateEditForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            self._setup_date_fields()
    
    def _setup_date_fields(self):
        restrictions = ServiceDateManager.get_date_edit_restrictions(self.instance)
        
        if not restrictions['can_edit_dates']:
            self._disable_date_fields(restrictions['restriction_reason'])
        else:
            self._setup_editable_date_fields(restrictions)
    
    def _disable_date_fields(self, reason: str):
        if 'start_date' in self.fields:
            self.fields['start_date'].disabled = True
            self.fields['start_date'].help_text = reason
        
        if 'end_date' in self.fields:
            self.fields['end_date'].disabled = True
            self.fields['end_date'].help_text = reason
    
    def _setup_editable_date_fields(self, restrictions: dict):
        if restrictions['has_payments'] and restrictions['restriction_reason']:
            for field in ['start_date', 'end_date']:
                if field in self.fields:
                    self.fields[field].help_text = restrictions['restriction_reason']
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.instance and self.instance.pk:
            start_date = cleaned_data.get('start_date')
            end_date = cleaned_data.get('end_date')
            
            if start_date and end_date and start_date >= end_date:
                raise forms.ValidationError({
                    'end_date': 'La fecha de finalización debe ser posterior a la fecha de inicio.'
                })
            
            restrictions = ServiceDateManager.get_date_edit_restrictions(self.instance)
            if not restrictions['can_edit_dates']:
                if start_date != self.instance.start_date or end_date != self.instance.end_date:
                    raise forms.ValidationError(
                        'No se pueden modificar las fechas: ' + restrictions['restriction_reason']
                    )
        
        return cleaned_data
    
    class Meta:
        model = ClientService
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
