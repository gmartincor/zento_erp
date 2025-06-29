from django import forms
from datetime import date
from django.utils import timezone

from ..models import ClientService


class ServiceDateEditForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            self._setup_date_fields()
    
    def _setup_date_fields(self):
        if self.instance.payments.exists():
            self._disable_date_fields("No se puede modificar la fecha de inicio porque el servicio tiene períodos asociados")
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
            
            if self.instance.payments.exists():
                if start_date != self.instance.start_date:
                    raise forms.ValidationError(
                        'No se puede modificar la fecha de inicio porque el servicio tiene períodos asociados'
                    )
        
        return cleaned_data
    
    class Meta:
        model = ClientService
        fields = ['start_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
