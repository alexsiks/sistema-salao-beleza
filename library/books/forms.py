from django import forms
from .models import Book, Comment, Category


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'publisher', 'year', 'description',
                  'cover_image', 'categories', 'total_copies']
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
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'categories': forms.CheckboxSelectMultiple(),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        labels = {'content': 'Seu comentário'}
        widgets = {'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escreva seu comentário...'})}
