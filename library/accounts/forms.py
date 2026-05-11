from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile


class RegisterForm(UserCreationForm):
    email      = forms.EmailField(required=True, label='E-mail')
    first_name = forms.CharField(max_length=50, required=True, label='Nome')
    last_name  = forms.CharField(max_length=50, required=True, label='Sobrenome')
    gender     = forms.ChoiceField(choices=[('', '— Selecione —')] + UserProfile.GENDER_CHOICES,
                                   required=True, label='Sexo')
    birth_date = forms.DateField(required=True, label='Data de Nascimento',
                                 widget=forms.DateInput(attrs={'type': 'date'}))
    phone      = forms.CharField(max_length=20, required=True, label='Telefone')
    cep        = forms.CharField(max_length=9,   required=True, label='CEP')
    logradouro = forms.CharField(max_length=200, required=True, label='Logradouro')
    numero     = forms.CharField(max_length=10,  required=True, label='Número')
    complemento= forms.CharField(max_length=100, required=False, label='Complemento')
    bairro     = forms.CharField(max_length=100, required=True, label='Bairro')
    cidade     = forms.CharField(max_length=100, required=True, label='Cidade')
    estado     = forms.CharField(max_length=2,   required=True, label='Estado')

    class Meta:
        model  = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email      = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True, label='Nome')
    last_name  = forms.CharField(max_length=50, required=True, label='Sobrenome')
    email      = forms.EmailField(required=True,               label='E-mail')
    phone      = forms.CharField(max_length=20, required=True, label='Telefone')

    class Meta:
        model  = UserProfile
        fields = ('gender', 'birth_date', 'phone', 'cep', 'logradouro', 'numero',
                  'complemento', 'bairro', 'cidade', 'estado', 'bio')
        labels = {
            'gender':      'Sexo',
            'birth_date':  'Data de Nascimento',
            'phone':       'Telefone',
            'cep':         'CEP',
            'logradouro':  'Logradouro',
            'numero':      'Número',
            'complemento': 'Complemento',
            'bairro':      'Bairro',
            'cidade':      'Cidade',
            'estado':      'Estado',
            'bio':         'Sobre mim',
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for field in ('cep', 'logradouro', 'numero', 'bairro', 'cidade', 'estado', 'gender', 'birth_date'):
            self.fields[field].required = True
        self.fields['complemento'].required = False
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial  = user.last_name
            self.fields['email'].initial      = user.email
