"""
Endpoints de análise de dados para integração com ferramentas de BI (Power BI, Tableau, etc.).
Todos os endpoints retornam JSON plano e requerem autenticação por Token.
Administradores têm acesso a todos os dados; usuários comuns veem apenas seus próprios dados.
"""
from datetime import date, timedelta
from django.db.models import Count, Avg, Q
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from books.models import Book, Reservation, Comment, Rating, Category
from accounts.models import ActionLog, UserProfile


class AnalyticsBooksView(APIView):
    """
    GET /api/analytics/books/
    Retorna todos os livros com estatísticas de reservas e avaliações.
    Ideal para: relatório de acervo, popularidade por categoria, disponibilidade.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        books = Book.objects.prefetch_related('categories', 'ratings', 'reservations').annotate(
            total_reservations=Count('reservations'),
            active_reservations=Count('reservations', filter=Q(reservations__status__in=['PENDING', 'ACTIVE'])),
            avg_rating=Avg('ratings__score'),
            total_ratings=Count('ratings'),
            total_comments=Count('comments'),
        )
        data = []
        for b in books:
            cats = ', '.join(b.categories.values_list('name', flat=True))
            data.append({
                'id':                  b.id,
                'titulo':              b.title,
                'autor':               b.author,
                'editora':             b.publisher or '',
                'ano':                 b.year,
                'isbn':                b.isbn or '',
                'categorias':          cats,
                'total_exemplares':    b.total_copies,
                'exemplares_disponiveis': b.available_copies,
                'disponivel':          b.available_copies > 0,
                'total_reservas':      b.total_reservations,
                'reservas_ativas':     b.active_reservations,
                'media_avaliacao':     round(b.avg_rating, 2) if b.avg_rating else None,
                'total_avaliacoes':    b.total_ratings,
                'total_comentarios':   b.total_comments,
                'cadastrado_em':       b.created_at.strftime('%Y-%m-%d'),
            })
        return Response({'count': len(data), 'results': data})


class AnalyticsReservationsView(APIView):
    """
    GET /api/analytics/reservations/
    Retorna todas as reservas com detalhes de usuário e livro.
    Ideal para: análise temporal, taxa de cancelamento, tempo de retirada.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Reservation.objects.select_related('user', 'book', 'user__profile')
        if not request.user.is_staff:
            qs = qs.filter(user=request.user)
        data = []
        for r in qs.order_by('-reserved_at'):
            profile = getattr(r.user, 'profile', None)
            data.append({
                'id':              r.id,
                'usuario_id':      r.user_id,
                'usuario':         r.user.username,
                'nome_completo':   r.user.get_full_name(),
                'cidade_usuario':  profile.cidade if profile else '',
                'estado_usuario':  profile.estado if profile else '',
                'livro_id':        r.book_id,
                'livro':           r.book.title,
                'autor':           r.book.author,
                'status':          r.status,
                'status_descricao':r.get_status_display(),
                'data_reserva':    r.reserved_at.strftime('%Y-%m-%d'),
                'hora_reserva':    r.reserved_at.strftime('%H:%M'),
                'prazo_retirada':  r.pickup_deadline.strftime('%Y-%m-%d') if r.pickup_deadline else None,
                'data_devolucao':  r.returned_at.strftime('%Y-%m-%d') if r.returned_at else None,
            })
        return Response({'count': len(data), 'results': data})


class AnalyticsRatingsView(APIView):
    """
    GET /api/analytics/ratings/
    Retorna todas as avaliações com dados de usuário e livro.
    Ideal para: análise de satisfação, NPS, correlação avaliação x reservas.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Rating.objects.select_related('user', 'book')
        if not request.user.is_staff:
            qs = qs.filter(user=request.user)
        data = []
        for r in qs.order_by('-created_at'):
            data.append({
                'id':          r.id,
                'usuario_id':  r.user_id,
                'usuario':     r.user.username,
                'livro_id':    r.book_id,
                'livro':       r.book.title,
                'autor':       r.book.author,
                'nota':        r.score,
                'data':        r.created_at.strftime('%Y-%m-%d'),
            })
        return Response({'count': len(data), 'results': data})


class AnalyticsUsersView(APIView):
    """
    GET /api/analytics/users/
    Retorna todos os usuários com dados de perfil e atividade. (Somente admin)
    Ideal para: perfil demográfico, engajamento por região, segmentação.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        users = User.objects.select_related('profile').annotate(
            total_reservas=Count('reservations'),
            reservas_ativas=Count('reservations', filter=Q(reservations__status__in=['PENDING', 'ACTIVE'])),
            total_comentarios=Count('comments'),
            total_avaliacoes=Count('ratings'),
        ).order_by('-date_joined')
        data = []
        for u in users:
            p = getattr(u, 'profile', None)
            data.append({
                'id':                 u.id,
                'username':           u.username,
                'nome':               u.first_name,
                'sobrenome':          u.last_name,
                'nome_completo':      u.get_full_name(),
                'email':              u.email,
                'sexo':               p.get_gender_display() if p and p.gender else '',
                'data_nascimento':    p.birth_date.strftime('%Y-%m-%d') if p and p.birth_date else None,
                'idade':              p.age if p else None,
                'telefone':           p.phone if p else '',
                'cep':                p.cep if p else '',
                'cidade':             p.cidade if p else '',
                'estado':             p.estado if p else '',
                'bairro':             p.bairro if p else '',
                'admin':              u.is_staff,
                'ativo':              u.is_active,
                'data_cadastro':      u.date_joined.strftime('%Y-%m-%d'),
                'ultimo_login':       u.last_login.strftime('%Y-%m-%d') if u.last_login else None,
                'total_reservas':     u.total_reservas,
                'reservas_ativas':    u.reservas_ativas,
                'total_comentarios':  u.total_comentarios,
                'total_avaliacoes':   u.total_avaliacoes,
            })
        return Response({'count': len(data), 'results': data})


class AnalyticsLogsView(APIView):
    """
    GET /api/analytics/logs/
    Retorna os logs de ações agrupados por tipo e período. (Somente admin)
    Ideal para: monitoramento de uso, auditoria, análise de comportamento.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        qs = ActionLog.objects.select_related('user').order_by('-timestamp')[:2000]
        data = []
        for lg in qs:
            data.append({
                'id':            lg.id,
                'usuario_id':    lg.user_id,
                'usuario':       lg.user.username if lg.user else '',
                'acao':          lg.action,
                'acao_descricao':lg.get_action_display(),
                'descricao':     lg.description,
                'ip':            lg.ip_address or '',
                'caminho':       lg.path,
                'metodo':        lg.method,
                'data':          lg.timestamp.strftime('%Y-%m-%d'),
                'hora':          lg.timestamp.strftime('%H:%M:%S'),
                'timestamp_iso': lg.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
            })
        return Response({'count': len(data), 'results': data})


class AnalyticsSummaryView(APIView):
    """
    GET /api/analytics/summary/
    KPIs gerais do sistema em um único endpoint.
    Ideal para: dashboard executivo, card de resumo no Power BI.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        today = date.today()
        last_30 = today - timedelta(days=30)
        last_7  = today - timedelta(days=7)

        total_books        = Book.objects.count()
        available_books    = Book.objects.filter(available_copies__gt=0).count()
        total_users        = User.objects.filter(is_active=True).count()
        total_reservations = Reservation.objects.count()
        active_res         = Reservation.objects.filter(status__in=['PENDING', 'ACTIVE']).count()
        cancelled_res      = Reservation.objects.filter(status='CANCELLED').count()
        returned_res       = Reservation.objects.filter(status='RETURNED').count()
        res_last_30        = Reservation.objects.filter(reserved_at__date__gte=last_30).count()
        res_last_7         = Reservation.objects.filter(reserved_at__date__gte=last_7).count()
        avg_rating         = Rating.objects.aggregate(avg=Avg('score'))['avg']
        total_ratings      = Rating.objects.count()
        total_comments     = Comment.objects.count()
        logins_last_30     = ActionLog.objects.filter(action='LOGIN', timestamp__date__gte=last_30).count()
        new_users_last_30  = User.objects.filter(date_joined__date__gte=last_30).count()
        categories         = Category.objects.count()

        # Livro mais reservado
        top_book = (
            Book.objects.annotate(n=Count('reservations'))
            .order_by('-n').first()
        )

        return Response({
            'data_referencia':         today.strftime('%Y-%m-%d'),
            'acervo': {
                'total_livros':        total_books,
                'livros_disponiveis':  available_books,
                'livros_indisponiveis':total_books - available_books,
                'total_categorias':    categories,
            },
            'usuarios': {
                'total_usuarios':      total_users,
                'novos_ultimos_30dias':new_users_last_30,
                'logins_ultimos_30dias':logins_last_30,
            },
            'reservas': {
                'total':               total_reservations,
                'ativas':              active_res,
                'devolvidas':          returned_res,
                'canceladas':          cancelled_res,
                'ultimos_30dias':      res_last_30,
                'ultimos_7dias':       res_last_7,
            },
            'avaliacoes': {
                'total':               total_ratings,
                'media_geral':         round(avg_rating, 2) if avg_rating else None,
                'total_comentarios':   total_comments,
            },
            'destaque': {
                'livro_mais_reservado':top_book.title if top_book else None,
                'reservas_livro_top':  top_book.n if top_book else 0,
            },
        })


class AnalyticsCategoriesView(APIView):
    """
    GET /api/analytics/categories/
    Estatísticas por categoria de livro.
    Ideal para: treemap de categorias, análise de demanda por gênero.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cats = Category.objects.annotate(
            total_livros=Count('book'),
            total_reservas=Count('book__reservations'),
            media_avaliacao=Avg('book__ratings__score'),
        )
        data = []
        for c in cats:
            data.append({
                'id':              c.id,
                'categoria':       c.name,
                'total_livros':    c.total_livros,
                'total_reservas':  c.total_reservas,
                'media_avaliacao': round(c.media_avaliacao, 2) if c.media_avaliacao else None,
            })
        data.sort(key=lambda x: x['total_reservas'], reverse=True)
        return Response({'count': len(data), 'results': data})
