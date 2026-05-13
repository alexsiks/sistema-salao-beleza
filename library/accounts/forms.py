from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile


_INPUT = 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-primary'
_SELECT = 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-primary bg-white'


class RegisterForm(UserCreationForm):
    email      = forms.EmailField(required=True, label='E-mail',
                                  widget=forms.EmailInput(attrs={'class': _INPUT, 'placeholder': 'seu@email.com'}))
    first_name = forms.CharField(max_length=50, required=True, label='Nome',
                                 widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Seu nome'}))
    last_name  = forms.CharField(max_length=50, required=True, label='Sobrenome',
                                 widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Seu sobrenome'}))
    gender     = forms.ChoiceField(choices=[('', '— Selecione —')] + UserProfile.GENDER_CHOICES,
                                   required=True, label='Sexo',
                                   widget=forms.Select(attrs={'class': _SELECT}))
    birth_date = forms.DateField(required=True, label='Data de Nascimento',
                                 widget=forms.DateInput(attrs={'type': 'date', 'class': _INPUT}))
    phone      = forms.CharField(max_length=20, required=True, label='Telefone',
                                 widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': '(00) 00000-0000'}))
    cep        = forms.CharField(max_length=9, required=True, label='CEP',
                                 widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': '00000-000', 'id': 'id_cep'}))
    logradouro = forms.CharField(max_length=200, required=True, label='Logradouro',
                                 widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Rua, Avenida...', 'id': 'id_logradouro'}))
    numero     = forms.CharField(max_length=10, required=True, label='Número',
                                 widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Ex: 123', 'id': 'id_numero'}))
    complemento= forms.CharField(max_length=100, required=False, label='Complemento',
                                 widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Apto, Bloco... (opcional)', 'id': 'id_complemento'}))
    bairro     = forms.CharField(max_length=100, required=True, label='Bairro',
                                 widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Bairro', 'id': 'id_bairro'}))
    cidade     = forms.CharField(max_length=100, required=True, label='Cidade',
                                 widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Cidade', 'id': 'id_cidade'}))
    estado     = forms.CharField(max_length=2, required=True, label='UF',
                                 widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'SP', 'maxlength': '2', 'id': 'id_estado'}))

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
