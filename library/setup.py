"""
Setup script: creates migrations, applies them, creates superuser, and seeds sample data.
Run with: python setup.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from books.models import Category, Book
from accounts.models import ActionLog

print("=== Configurando o Sistema de Biblioteca ===\n")

print("1. Criando migrações...")
call_command('makemigrations', '--verbosity=0')
call_command('migrate', '--verbosity=1')
print()

print("2. Criando superusuário administrador...")
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@biblioteca.com',
        password='admin123',
        first_name='Administrador',
        last_name='Sistema'
    )
    print(f"   ✓ Admin criado: admin / admin123")
else:
    print("   → Admin já existe.")

print("\n3. Criando categorias de exemplo...")
cats = ['Romance', 'Ficção Científica', 'História', 'Tecnologia', 'Filosofia',
        'Biografia', 'Poesia', 'Terror', 'Aventura', 'Autoajuda']
created = 0
for name in cats:
    _, c = Category.objects.get_or_create(name=name)
    if c:
        created += 1
print(f"   ✓ {created} categorias criadas / {len(cats) - created} já existiam.")

print("\n4. Criando livros de exemplo...")
admin_user = User.objects.get(username='admin')
sample_books = [
    {
        'title': 'Dom Casmurro',
        'author': 'Machado de Assis',
        'publisher': 'Garnier',
        'year': 1899,
        'description': 'Romance brasileiro do Realismo, narra a história de Bentinho e Capitu, '
                       'explorando temas como ciúme, memória e dúvida.',
        'total_copies': 3,
        'categories': ['Romance'],
    },
    {
        'title': 'O Guia do Mochileiro das Galáxias',
        'author': 'Douglas Adams',
        'publisher': 'Sextante',
        'year': 1979,
        'description': 'Ficção científica cômica sobre Arthur Dent, um inglês comum que percorre '
                       'a galáxia após a destruição da Terra.',
        'total_copies': 2,
        'categories': ['Ficção Científica', 'Aventura'],
    },
    {
        'title': 'Sapiens: Uma Breve História da Humanidade',
        'author': 'Yuval Noah Harari',
        'publisher': 'Companhia das Letras',
        'year': 2011,
        'description': 'Traça a história da humanidade desde os primórdios da espécie humana '
                       'até o presente, analisando como o Homo sapiens dominou o planeta.',
        'total_copies': 4,
        'categories': ['História'],
    },
    {
        'title': 'Clean Code',
        'author': 'Robert C. Martin',
        'publisher': 'Alta Books',
        'year': 2008,
        'description': 'Manual de boas práticas para escrever código limpo, legível e '
                       'sustentável. Indispensável para programadores profissionais.',
        'total_copies': 2,
        'categories': ['Tecnologia'],
    },
    {
        'title': 'O Senhor dos Anéis',
        'author': 'J.R.R. Tolkien',
        'publisher': 'HarperCollins',
        'year': 1954,
        'description': 'Épica fantasia que narra a jornada de Frodo Bolseiro para destruir '
                       'o Um Anel e salvar a Terra-média.',
        'total_copies': 3,
        'categories': ['Aventura', 'Ficção Científica'],
    },
]

for data in sample_books:
    if not Book.objects.filter(title=data['title']).exists():
        cats_list = data.pop('categories')
        book = Book.objects.create(
            created_by=admin_user,
            available_copies=data['total_copies'],
            **data
        )
        for cat_name in cats_list:
            cat = Category.objects.get(name=cat_name)
            book.categories.add(cat)
        print(f"   ✓ {book.title}")

print("\n=== Setup concluído! ===")
print(f"\n  URL:   http://localhost:8000")
print(f"  Admin: http://localhost:8000/admin")
print(f"  Login: admin / admin123")
print(f"\n  API: http://localhost:8000/api/")
print(f"  Documentação da API: veja /api/auth/login/, /api/books/, etc.")
