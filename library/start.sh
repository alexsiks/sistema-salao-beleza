#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== Iniciando Sistema de Agendamento de Salão ==="

# Use the project Python (3.11 with all dependencies installed)
PYTHON="${PYTHONLIBS_HOME:-/home/runner/workspace/.pythonlibs}/bin/python"
if [ ! -f "$PYTHON" ]; then
    PYTHON="python"
fi

# Run migrations
$PYTHON manage.py makemigrations --verbosity=0 2>/dev/null || true
$PYTHON manage.py migrate --verbosity=0

# Create superuser if not exists
$PYTHON -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca.settings')
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@salao.com', 'admin123', first_name='Administrador', last_name='Salão')
    print('Admin criado: admin / admin123')
"

# Seed salon data
$PYTHON -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca.settings')
django.setup()
from books.models import SalonConfig, ServiceCategory, Service, Professional
from django.contrib.auth.models import User

# Singleton config
config = SalonConfig.get()
if config.salon_name == 'Espaço Beleza':
    config.salon_name = 'Espaço Beleza'
    config.phone = '(11) 99999-0000'
    config.address = 'Rua das Flores, 123 — São Paulo, SP'
    config.save()
    print('Configuração do salão criada.')

# Categories
cats_data = [
    ('Cabelo', 'bi-scissors'),
    ('Unhas', 'bi-star'),
    ('Estética', 'bi-flower1'),
    ('Maquiagem', 'bi-brush'),
    ('Sobrancelha', 'bi-eye'),
    ('Massagem', 'bi-heart-pulse'),
]
cats = {}
for name, icon in cats_data:
    cat, _ = ServiceCategory.objects.get_or_create(name=name, defaults={'icon': icon})
    cats[name] = cat

# Services
services_data = [
    ('Corte Feminino', 'Corte personalizado para cabelos femininos. Inclui lavagem, corte e finalização básica.', 60, '80.00', 'Cabelo'),
    ('Corte Masculino', 'Corte moderno para cabelos masculinos com finalização.', 30, '45.00', 'Cabelo'),
    ('Coloração / Tintura', 'Aplicação de coloração ou tonalizante. Preço pode variar conforme comprimento.', 120, '150.00', 'Cabelo'),
    ('Escova Progressiva', 'Alisamento duradouro com escova progressiva. Reduz frizz e facilita a modelagem.', 180, '250.00', 'Cabelo'),
    ('Hidratação Capilar', 'Tratamento intensivo de hidratação para cabelos ressecados e danificados.', 60, '90.00', 'Cabelo'),
    ('Manicure', 'Cuidado completo das unhas das mãos: limpeza, corte, lixa e esmaltação.', 45, '40.00', 'Unhas'),
    ('Pedicure', 'Cuidado completo das unhas dos pés: limpeza, corte, lixa e esmaltação.', 50, '50.00', 'Unhas'),
    ('Manicure + Pedicure', 'Pacote completo de cuidados para mãos e pés.', 90, '80.00', 'Unhas'),
    ('Gel nos dedos', 'Aplicação de gel nas unhas para maior resistência e duração.', 90, '120.00', 'Unhas'),
    ('Design de Sobrancelhas', 'Modelagem e definição das sobrancelhas com pinça e linha.', 30, '35.00', 'Sobrancelha'),
    ('Henna de Sobrancelhas', 'Coloração das sobrancelhas com henna para mais definição e volume.', 30, '50.00', 'Sobrancelha'),
    ('Limpeza de Pele', 'Limpeza profunda dos poros com extração de cravos e esfoliação.', 60, '120.00', 'Estética'),
    ('Maquiagem Social', 'Maquiagem completa para eventos sociais, formaturas e festas.', 60, '150.00', 'Maquiagem'),
    ('Massagem Relaxante', 'Massagem corporal completa para alívio de tensões e estresse.', 60, '130.00', 'Massagem'),
]
for name, desc, duration, price, cat_name in services_data:
    svc, created = Service.objects.get_or_create(
        name=name,
        defaults={
            'description': desc,
            'duration_minutes': duration,
            'price': price,
            'category': cats.get(cat_name),
            'is_active': True,
        }
    )
    if created:
        print(f'Serviço criado: {name}')

# Create professional users and profiles
professionals_data = [
    ('ana_silva', 'Ana', 'Silva', 'ana@salao.com', 'Especialista em coloração e tratamentos capilares. 8 anos de experiência.',
     ['Corte Feminino', 'Coloração / Tintura', 'Escova Progressiva', 'Hidratação Capilar']),
    ('carlos_gomes', 'Carlos', 'Gomes', 'carlos@salao.com', 'Barbeiro e cabeleireiro masculino. Especialidade em cortes modernos.',
     ['Corte Masculino', 'Corte Feminino']),
    ('patricia_costa', 'Patrícia', 'Costa', 'patricia@salao.com', 'Manicure e pedicure com 5 anos de experiência. Especializada em nail art.',
     ['Manicure', 'Pedicure', 'Manicure + Pedicure', 'Gel nos dedos']),
    ('juliana_mendes', 'Juliana', 'Mendes', 'juliana@salao.com', 'Esteticista formada. Especialidade em limpeza de pele e cuidados faciais.',
     ['Limpeza de Pele', 'Design de Sobrancelhas', 'Henna de Sobrancelhas', 'Maquiagem Social']),
    ('marcos_lima', 'Marcos', 'Lima', 'marcos@salao.com', 'Massagista terapêutico com certificação em diversas técnicas de massagem.',
     ['Massagem Relaxante']),
]

for username, first, last, email, bio, service_names in professionals_data:
    user, created_user = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': first,
            'last_name': last,
            'email': email,
            'is_staff': False,
            'is_active': True,
        }
    )
    if created_user:
        user.set_password('prof123')
        user.save()

    prof, created_prof = Professional.objects.get_or_create(user=user, defaults={'bio': bio, 'is_active': True})
    if not created_prof:
        prof.bio = bio
        prof.is_active = True
        prof.save()

    for svc_name in service_names:
        try:
            svc = Service.objects.get(name=svc_name)
            prof.services.add(svc)
        except Service.DoesNotExist:
            pass

    if created_prof:
        print(f'Profissional criado: {first} {last}')
"

# Create media directories
mkdir -p media/servicos media/profissionais

echo "=== Iniciando servidor na porta 5000 ==="
PORT=${PORT:-5000}
exec $PYTHON manage.py runserver 0.0.0.0:$PORT
