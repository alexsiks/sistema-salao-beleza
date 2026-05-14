"""
Setup script: creates migrations, applies them, creates a superuser, and seeds sample salon data.
Run with: python setup.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salao.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from servicos.models import SalonConfig, ServiceCategory, Service, Professional

print("=== Configurando o Sistema de Agendamento de Salão ===\n")

print("1. Criando migrações...")
call_command('makemigrations', '--verbosity=0')
call_command('migrate', '--verbosity=1')
print()

print("2. Criando superusuário administrador...")
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@salao.com',
        password='admin123',
        first_name='Administrador',
        last_name='Salão'
    )
    print(f"   ✓ Admin criado: admin / admin123")
else:
    print("   → Admin já existe.")

print("\n3. Criando configuração do salão...")
config = SalonConfig.get()
config.salon_name = 'Espaço Beleza'
config.phone = '(11) 99999-0000'
config.address = 'Rua das Flores, 123 — São Paulo, SP'
config.save()
print("   ✓ Configuração do salão criada.")

print("\n4. Criando categorias de serviços de exemplo...")
categories = [
    ('Cabelo', 'bi-scissors'),
    ('Unhas', 'bi-star'),
    ('Estética', 'bi-flower1'),
    ('Maquiagem', 'bi-brush'),
    ('Sobrancelha', 'bi-eye'),
    ('Massagem', 'bi-heart-pulse'),
]
for name, icon in categories:
    ServiceCategory.objects.get_or_create(name=name, defaults={'icon': icon})
print("   ✓ Categorias criadas.")

print("\n5. Criando serviços de exemplo...")
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
for name, description, duration, price, category_name in services_data:
    category = ServiceCategory.objects.get(name=category_name)
    Service.objects.get_or_create(
        name=name,
        defaults={
            'description': description,
            'duration_minutes': duration,
            'price': price,
            'category': category,
            'is_active': True,
        }
    )
print("   ✓ Serviços criados.")

print("\n6. Criando profissionais de exemplo...")
professionals_data = [
    ('ana_silva', 'Ana', 'Silva', 'ana@salao.com', 'Especialista em coloração e tratamentos capilares. 8 anos de experiência.', ['Corte Feminino', 'Coloração / Tintura', 'Escova Progressiva', 'Hidratação Capilar']),
    ('carlos_gomes', 'Carlos', 'Gomes', 'carlos@salao.com', 'Barbeiro e cabeleireiro masculino. Especialidade em cortes modernos.', ['Corte Masculino', 'Corte Feminino']),
    ('patricia_costa', 'Patrícia', 'Costa', 'patricia@salao.com', 'Manicure e pedicure com 5 anos de experiência. Especializada em nail art.', ['Manicure', 'Pedicure', 'Manicure + Pedicure', 'Gel nos dedos']),
    ('juliana_mendes', 'Juliana', 'Mendes', 'juliana@salao.com', 'Esteticista formada. Especialidade em limpeza de pele e cuidados faciais.', ['Limpeza de Pele', 'Design de Sobrancelhas', 'Henna de Sobrancelhas', 'Maquiagem Social']),
    ('marcos_lima', 'Marcos', 'Lima', 'marcos@salao.com', 'Massagista terapêutico com certificação em diversas técnicas de massagem.', ['Massagem Relaxante']),
]
for username, first_name, last_name, email, bio, service_names in professionals_data:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'is_active': True,
        }
    )
    if created:
        user.set_password('prof123')
        user.save()
    prof, _ = Professional.objects.get_or_create(user=user, defaults={'bio': bio, 'is_active': True})
    if prof.bio != bio:
        prof.bio = bio
        prof.save()
    for svc_name in service_names:
        try:
            service = Service.objects.get(name=svc_name)
            prof.services.add(service)
        except Service.DoesNotExist:
            continue
print("   ✓ Profissionais criados.")

print("\n=== Setup concluído! ===")
print(f"\n  URL:   http://localhost:8000")
print(f"  Admin: http://localhost:8000/admin")
print(f"  Login: admin / admin123")
print(f"\n  API: http://localhost:8000/api/")
print(f"  Documentação da API: veja /api/auth/login/, /api/servicos/, etc.")
