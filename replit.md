# Sistema de Biblioteca

Sistema web completo de gestão de biblioteca com Django, SQLite e API REST com autenticação por token.

## Run & Operate

- `bash library/start.sh` — inicia o servidor Django (porta 8000)
- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)

## Stack

- **Backend:** Python 3.11 + Django 5.2 + SQLite
- **API REST:** Django REST Framework com autenticação por Token
- **Frontend:** Django Templates + Bootstrap 5.3
- **Consulta CEP:** ViaCEP (API pública)
- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Build: esbuild (CJS bundle)

## Acesso Padrão

- **URL:** http://localhost:8000
- **Admin Django:** http://localhost:8000/admin
- **API REST:** http://localhost:8000/api/
- **Login padrão:** admin / admin123

## Onde as coisas ficam

```
library/
├── biblioteca/        # Configurações Django (settings, urls, wsgi)
├── accounts/          # App de usuários (modelos, views, API, serializers)
│   ├── models.py      # UserProfile, ActionLog
│   ├── views.py       # Login, Register, Profile, CEP lookup
│   ├── api_views.py   # API endpoints de autenticação e usuários
│   └── middleware.py  # Registro automático de ações
├── books/             # App de livros (modelos, views, API, serializers)
│   ├── models.py      # Book, Category, Reservation, Comment, Rating
│   ├── views.py       # CRUD de livros, reservas, comentários, avaliações
│   └── api_views.py   # API endpoints de livros
├── templates/         # Templates HTML (Bootstrap 5)
├── media/             # Imagens de capas dos livros
├── requirements.txt   # Dependências Python
└── start.sh           # Script de inicialização (migrations + seed + runserver)
```

## API REST — Endpoints Principais

### Autenticação
- `POST /api/auth/register/` — Cadastrar novo usuário
- `POST /api/auth/login/` — Login (retorna token)
- `POST /api/auth/logout/` — Logout (invalida token)
- `GET  /api/auth/token/` — Ver token atual

### Usuários (admin)
- `GET  /api/users/` — Listar usuários
- `GET  /api/users/me/` — Ver perfil próprio
- `PUT  /api/users/me/profile/` — Atualizar perfil

### Livros
- `GET  /api/books/` — Listar livros (com filtros: q, category, available)
- `GET  /api/books/<id>/` — Detalhes do livro
- `POST /api/books/` — Criar livro (admin)
- `POST /api/books/<id>/reserve/` — Reservar livro
- `POST /api/books/<id>/comment/` — Comentar livro
- `POST /api/books/<id>/rate/` — Avaliar livro (1-5)

### Reservas
- `GET  /api/reservations/` — Listar reservas
- `POST /api/reservations/<id>/cancel/` — Cancelar reserva

### Logs (admin)
- `GET  /api/logs/` — Logs de ações dos usuários

## Architecture decisions

- Token individual por usuário via DRF TokenAuthentication
- Middleware de log automático de ações POST
- Sinal post_save para criação automática de UserProfile
- Busca de CEP via ViaCEP API (gratuita, sem chave)
- Imagens de capa armazenadas em media/books/
- Paginação de 10 itens por página na API

## Product

Sistema de biblioteca com:
- Acervo de livros com imagem de capa, categorias, descrição
- Reserva de livros com controle de exemplares disponíveis
- Comentários e avaliações (1-5 estrelas) por livro
- Painel administrativo completo (Django Admin)
- API REST documentada com autenticação por token individual
- Registro completo de ações dos usuários (logs)
- Busca de endereço por CEP (ViaCEP) no perfil do usuário

## User preferences

- Stack: Python + Django + SQLite

## Gotchas

- Sempre rodar `start.sh` a partir da raiz do workspace (`bash library/start.sh`)
- O script de startup aplica migrations automaticamente
- Admin padrão: admin / admin123 (trocar em produção)
- Usar header `Authorization: Token <seu_token>` nas chamadas da API

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
