from django import forms
from django.core.exceptions import ValidationError

from apps.accounting.models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['full_name', 'dni', 'gender', 'email', 'phone', 'notes', 'is_active']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'gender': forms.Select(),
        }
    
    def clean_dni(self):
        dni = self.cleaned_data['dni'].strip().upper()
        if len(dni) != 9:
            raise ValidationError('El DNI debe tener 9 caracteres')
        return dni
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email and '@' not in email:
            raise ValidationError('Formato de email inválido')
        return email


class ClientCreateForm(ClientForm):
    def clean_dni(self):
        dni = super().clean_dni()
        if Client.objects.filter(dni=dni).exists():
            raise ValidationError(f'Ya existe un cliente con el DNI {dni}')
        return dni


class ClientUpdateForm(ClientForm):
    def clean_dni(self):
        dni = super().clean_dni()
        if self.instance and self.instance.pk:
            if Client.objects.filter(dni=dni).exclude(pk=self.instance.pk).exists():
                raise ValidationError(f'Ya existe otro cliente con el DNI {dni}')
        return dni
