from django import forms
from django.contrib.auth.models import User
from .models import Service, ServiceCategory, Professional, Appointment, SalonConfig


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'duration_minutes', 'price',
                  'category', 'image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'duration_minutes': forms.NumberInput(attrs={'min': '1'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }


class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'icon', 'description']


class ProfessionalForm(forms.ModelForm):
    first_name = forms.CharField(label='Primeiro Nome', max_length=150)
    last_name = forms.CharField(label='Sobrenome', max_length=150, required=False)
    email = forms.EmailField(label='E-mail', required=False)

    class Meta:
        model = Professional
        fields = ['bio', 'photo', 'services', 'is_active']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'services': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            u = self.instance.user
            self.fields['first_name'].initial = u.first_name
            self.fields['last_name'].initial = u.last_name
            self.fields['email'].initial = u.email

    def save(self, commit=True):
        professional = super().save(commit=False)
        professional.user.first_name = self.cleaned_data['first_name']
        professional.user.last_name = self.cleaned_data.get('last_name', '')
        professional.user.email = self.cleaned_data.get('email', '')
        professional.user.save()
        if commit:
            professional.save()
            self.save_m2m()
        return professional


class AppointmentBookingForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['professional', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3,
                                           'placeholder': 'Alguma observação? (opcional)'}),
        }

    def __init__(self, service=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['professional'].queryset = (
            Professional.objects.filter(is_active=True, services=service)
            if service else Professional.objects.filter(is_active=True)
        )
        self.fields['professional'].empty_label = 'Sem preferência (qualquer profissional)'
        self.fields['professional'].required = False


class SalonConfigForm(forms.ModelForm):
    class Meta:
        model = SalonConfig
        fields = ['salon_name', 'phone', 'address',
                  'open_time', 'close_time', 'slot_minutes',
                  'max_advance_days', 'cancellation_hours']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'open_time': forms.TimeInput(attrs={'type': 'time'}),
            'close_time': forms.TimeInput(attrs={'type': 'time'}),
        }
