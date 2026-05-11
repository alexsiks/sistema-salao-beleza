#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== Iniciando Sistema de Biblioteca ==="

# Run migrations
python manage.py makemigrations --verbosity=0 2>/dev/null || true
python manage.py migrate --verbosity=0

# Create superuser if not exists
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca.settings')
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@biblioteca.com', 'admin123', first_name='Administrador', last_name='Sistema')
    print('Admin criado: admin / admin123')
"

# Seed categories and books
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca.settings')
django.setup()
from books.models import Category, Book
from django.contrib.auth.models import User
cats = ['Romance', 'Ficção Científica', 'História', 'Tecnologia', 'Filosofia', 'Biografia', 'Poesia', 'Terror', 'Aventura', 'Autoajuda']
for name in cats:
    Category.objects.get_or_create(name=name)
admin = User.objects.get(username='admin')
books_data = [
    ('Dom Casmurro', 'Machado de Assis', 'Romance brasileiro do Realismo, narra a história de Bentinho e Capitu, explorando temas como ciúme, memória e dúvida.', 'Romance', 3),
    ('O Guia do Mochileiro das Galáxias', 'Douglas Adams', 'Ficção científica cômica sobre Arthur Dent que percorre a galáxia após a destruição da Terra.', 'Ficção Científica', 2),
    ('Sapiens: Uma Breve História da Humanidade', 'Yuval Noah Harari', 'Traça a história da humanidade desde os primórdios até o presente.', 'História', 4),
    ('Clean Code', 'Robert C. Martin', 'Manual de boas práticas para escrever código limpo, legível e sustentável.', 'Tecnologia', 2),
    ('O Senhor dos Anéis', 'J.R.R. Tolkien', 'Épica fantasia que narra a jornada de Frodo para destruir o Um Anel e salvar a Terra-média.', 'Aventura', 3),
]
for title, author, desc, cat_name, copies in books_data:
    if not Book.objects.filter(title=title).exists():
        book = Book.objects.create(title=title, author=author, description=desc, total_copies=copies, available_copies=copies, created_by=admin)
        cat = Category.objects.get(name=cat_name)
        book.categories.add(cat)
        print(f'Livro criado: {title}')
"

echo "=== Iniciando servidor na porta 5000 ==="
PORT=${PORT:-5000}
exec python manage.py runserver 0.0.0.0:$PORT
