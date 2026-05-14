# Sistema de Agendamento — Espaço Beleza

Sistema web completo de agendamento de salão de beleza com Django, SQLite e API REST com autenticação por token.

## Run & Operate

- `bash library/start.sh` — inicia o servidor Django (porta 5000)

## Stack

- **Backend:** Python 3.11 + Django 5.2 + SQLite
- **API REST:** Django REST Framework com autenticação por Token
- **Frontend:** Django Templates + Bootstrap 5.3

## Acesso Padrão

- **URL:** http://localhost:5000
- **Admin Django:** http://localhost:5000/admin
- **API REST:** http://localhost:5000/api/
- **Login padrão:** admin / admin123
- **Profissionais demo:** ana_silva, carlos_gomes, patricia_costa, juliana_mendes, marcos_lima (senha: prof123)

## Onde as coisas ficam

```
library/
├── salao/        # Configurações Django (settings, urls, wsgi)
├── accounts/          # App de usuários (modelos, views, API, serializers)
│   ├── models.py      # UserProfile, ActionLog
│   ├── views.py       # Login, Register, Profile, CEP lookup
│   ├── api_views.py   # API endpoints de autenticação e usuários
│   └── middleware.py  # Registro automático de ações
├── servicos/             # App principal do salão (modelos, views, API)
│   ├── models.py      # SalonConfig, ServiceCategory, Service, Professional, Appointment
│   ├── views.py       # Catálogo, agendamento, agenda admin, configurações
│   ├── api_views.py   # API endpoints de serviços e agendamentos
│   ├── analytics_views.py  # Endpoints de BI/analytics
│   └── forms.py       # ServiceForm, SalonConfigForm, AppointmentBookingForm
├── templates/         # Templates HTML (Bootstrap 5, tema pink/rose)
├── media/             # Imagens (servicos/, profissionais/)
├── requirements.txt   # Dependências Python
└── start.sh           # Script de inicialização (migrations + seed + runserver)
```

## Fluxo de Agendamento

1. Cliente acessa `/servicos/` — vê catálogo de serviços com foto, preço e duração
2. Clica em "Agendar" → seleciona profissional (opcional) e data
3. Sistema carrega horários disponíveis via AJAX
4. Cliente escolhe horário e confirma → status inicial: **PENDENTE**
5. Admin confirma em `/servicos/agendamentos/` → status: **CONFIRMADO**
6. Após atendimento, admin marca como **CONCLUÍDO**

## Modelos Principais

- **SalonConfig** — singleton com horários de funcionamento, intervalo entre slots, antecedência mínima de cancelamento
- **ServiceCategory** — categorias (Cabelo, Unhas, Estética, etc.)
- **Service** — serviço com duração, preço, categoria, foto
- **Professional** — usuário com perfil de profissional, serviços que realiza
- **Appointment** — agendamento com status (PENDING / CONFIRMED / CANCELLED / COMPLETED / NO_SHOW)

## API REST — Endpoints Principais

### Autenticação
- `POST /api/auth/login/` — Login (retorna token)
- `POST /api/auth/register/` — Cadastrar novo usuário

### Serviços
- `GET /api/services/` — Listar serviços (filtros: q, category)
- `GET /api/services/<id>/` — Detalhes do serviço
- `GET /api/categories/` — Categorias

### Agendamento
- `GET /api/available-slots/?service=1&date=2025-06-15` — Horários disponíveis
- `GET /api/professionals/?service=1` — Profissionais para um serviço
- `POST /api/appointments/book/` — Criar agendamento
- `GET /api/appointments/` — Listar agendamentos do usuário
- `POST /api/appointments/<id>/cancel/` — Cancelar agendamento

### Administração (admin only)
- `POST /api/appointments/<id>/confirm/` — Confirmar
- `POST /api/appointments/<id>/complete/` — Concluir
- `GET /api/financial/` — Resumo financeiro
- `GET /api/analytics/summary/` — KPIs do salão

## User preferences

- Stack: Python + Django + SQLite
- Port: 5000
- Theme: Pink/Rose Gold (--salon-primary: #c2185b, --salon-accent: #f4a261)

## Gotchas

- Sempre rodar `start.sh` a partir da raiz do workspace (`bash library/start.sh`)
- O script aplica migrations e cria dados de seed automaticamente
- Horários disponíveis são calculados em tempo real via AJAX no momento do agendamento
- SalonConfig é singleton (pk=1) — configurar em `/servicos/configuracoes/`

## Serviços de Demo (criados pelo seed)

| Serviço | Duração | Preço | Profissional |
|---------|---------|-------|-------------|
| Corte Feminino | 1h | R$ 80 | Ana Silva |
| Corte Masculino | 30min | R$ 45 | Carlos Gomes |
| Coloração / Tintura | 2h | R$ 150 | Ana Silva |
| Manicure | 45min | R$ 40 | Patrícia Costa |
| Pedicure | 50min | R$ 50 | Patrícia Costa |
| Limpeza de Pele | 1h | R$ 120 | Juliana Mendes |
| Massagem Relaxante | 1h | R$ 130 | Marcos Lima |
