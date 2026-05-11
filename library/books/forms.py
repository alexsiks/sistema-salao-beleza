from django import forms
from .models import Book, Comment, Category, LibraryConfig


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'publisher', 'year', 'description',
                  'cover_image', 'categories', 'total_copies', 'rental_price']
        labels = {
            'title': 'Título',
            'author': 'Autor',
            'isbn': 'ISBN',
            'publisher': 'Editora',
            'year': 'Ano de Publicação',
            'description': 'Descrição',
            'cover_image': 'Imagem da Capa',
            'categories': 'Categorias',
            'total_copies': 'Total de Exemplares',
            'rental_price': 'Valor do Empréstimo (R$)',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'categories': forms.CheckboxSelectMultiple(),
            'rental_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        labels = {'content': 'Seu comentário'}
        widgets = {'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escreva seu comentário...'})}


class LibraryConfigForm(forms.ModelForm):
    class Meta:
        model = LibraryConfig
        fields = ['fine_per_day', 'max_loan_days']
        labels = {
            'fine_per_day': 'Multa por Dia de Atraso (R$)',
            'max_loan_days': 'Prazo Máximo de Empréstimo (dias)',
        }
        widgets = {
            'fine_per_day': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'max_loan_days': forms.NumberInput(attrs={'min': '1'}),
        }
