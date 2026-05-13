"""
Endpoints de análise de dados para integração com ferramentas de BI.
Todos os endpoints requerem autenticação por Token.
Administradores têm acesso a todos os dados; usuários comuns veem apenas os próprios.
"""
from datetime import date, timedelta
from django.db.models import Count, Avg, Q, Sum
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from books.models import Service, ServiceCategory, Appointment, Professional, SalonConfig
from accounts.models import ActionLog, UserProfile


class AnalyticsSummaryView(APIView):
    """
    GET /api/analytics/summary/
    KPIs gerais do salão: receita, agendamentos, taxas de ocupação.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        appts = Appointment.objects.all()
        completed = appts.filter(status='COMPLETED')

        receita_total = completed.aggregate(t=Sum('price_snapshot'))['t'] or 0
        receita_mes   = completed.filter(date__gte=month_start).aggregate(t=Sum('price_snapshot'))['t'] or 0
        receita_semana = completed.filter(date__gte=week_start).aggregate(t=Sum('price_snapshot'))['t'] or 0

        return Response({
            'data': str(today),
            'agendamentos_hoje': appts.filter(date=today).count(),
            'agendamentos_semana': appts.filter(date__gte=week_start).count(),
            'agendamentos_mes': appts.filter(date__gte=month_start).count(),
            'agendamentos_total': appts.count(),
            'pendentes': appts.filter(status='PENDING').count(),
            'confirmados': appts.filter(status='CONFIRMED').count(),
            'concluidos': appts.filter(status='COMPLETED').count(),
            'cancelados': appts.filter(status='CANCELLED').count(),
            'nao_compareceu': appts.filter(status='NO_SHOW').count(),
            'receita_total': str(receita_total),
            'receita_mes': str(receita_mes),
            'receita_semana': str(receita_semana),
            'total_servicos': Service.objects.filter(is_active=True).count(),
            'total_profissionais': Professional.objects.filter(is_active=True).count(),
            'total_clientes': User.objects.filter(is_active=True).count(),
        })


class AnalyticsServicesView(APIView):
    """
    GET /api/analytics/services/
    Todos os serviços com estatísticas de agendamentos e receita.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        services = Service.objects.annotate(
            total_agendamentos=Count('appointments'),
            concluidos=Count('appointments', filter=Q(appointments__status='COMPLETED')),
            cancelados=Count('appointments', filter=Q(appointments__status='CANCELLED')),
            receita=Sum('appointments__price_snapshot', filter=Q(appointments__status='COMPLETED')),
        ).select_related('category').order_by('-total_agendamentos')

        data = []
        for s in services:
            data.append({
                'id': s.id,
                'nome': s.name,
                'categoria': s.category.name if s.category else None,
                'duracao_min': s.duration_minutes,
                'preco': str(s.price),
                'ativo': s.is_active,
                'total_agendamentos': s.total_agendamentos,
                'concluidos': s.concluidos,
                'cancelados': s.cancelados,
                'receita': str(s.receita or 0),
                'profissionais': s.professionals.filter(is_active=True).count(),
            })
        return Response(data)


class AnalyticsCategoriesView(APIView):
    """
    GET /api/analytics/categories/
    Estatísticas por categoria de serviço.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cats = ServiceCategory.objects.annotate(
            total_servicos=Count('services', filter=Q(services__is_active=True)),
            total_agendamentos=Count('services__appointments'),
            receita=Sum('services__appointments__price_snapshot',
                        filter=Q(services__appointments__status='COMPLETED')),
        ).order_by('-total_agendamentos')

        data = []
        for c in cats:
            data.append({
                'id': c.id,
                'nome': c.name,
                'total_servicos': c.total_servicos,
                'total_agendamentos': c.total_agendamentos,
                'receita': str(c.receita or 0),
            })
        return Response(data)


class AnalyticsAppointmentsView(APIView):
    """
    GET /api/analytics/appointments/
    Todos os agendamentos com detalhes completos.
    Admin vê todos; clientes veem apenas os próprios.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Appointment.objects.select_related(
            'client', 'professional__user', 'service__category'
        ).order_by('-date', '-start_time')

        if not request.user.is_staff:
            qs = qs.filter(client=request.user)

        data = []
        for a in qs:
            data.append({
                'id': a.id,
                'cliente': a.client.get_full_name() or a.client.username,
                'cliente_username': a.client.username,
                'profissional': a.professional.full_name if a.professional else None,
                'servico': a.service.name,
                'categoria': a.service.category.name if a.service.category else None,
                'data': str(a.date),
                'hora_inicio': str(a.start_time),
                'hora_fim': str(a.end_time),
                'status': a.status,
                'status_display': a.get_status_display(),
                'preco': str(a.price_snapshot),
                'duracao_min': a.duration_snapshot,
                'observacoes': a.notes,
                'motivo_cancelamento': a.cancel_reason,
                'criado_em': a.created_at.isoformat(),
            })
        return Response(data)


class AnalyticsProfessionalsView(APIView):
    """
    GET /api/analytics/professionals/
    Desempenho por profissional. Admin only.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        profs = Professional.objects.select_related('user').prefetch_related('services').annotate(
            total_agendamentos=Count('appointments'),
            concluidos=Count('appointments', filter=Q(appointments__status='COMPLETED')),
            cancelados=Count('appointments', filter=Q(appointments__status='CANCELLED')),
            no_show=Count('appointments', filter=Q(appointments__status='NO_SHOW')),
            receita=Sum('appointments__price_snapshot', filter=Q(appointments__status='COMPLETED')),
        ).order_by('-total_agendamentos')

        data = []
        for p in profs:
            data.append({
                'id': p.id,
                'nome': p.full_name,
                'username': p.user.username,
                'ativo': p.is_active,
                'servicos': [s.name for s in p.services.all()],
                'total_agendamentos': p.total_agendamentos,
                'concluidos': p.concluidos,
                'cancelados': p.cancelados,
                'no_show': p.no_show,
                'receita': str(p.receita or 0),
            })
        return Response(data)


class AnalyticsUsersView(APIView):
    """
    GET /api/analytics/users/
    Clientes com histórico de agendamentos. Admin only.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        users = User.objects.select_related('profile').annotate(
            total_agendamentos=Count('appointments'),
            concluidos=Count('appointments', filter=Q(appointments__status='COMPLETED')),
            cancelados=Count('appointments', filter=Q(appointments__status='CANCELLED')),
            gasto_total=Sum('appointments__price_snapshot', filter=Q(appointments__status='COMPLETED')),
        ).order_by('-total_agendamentos')

        data = []
        for u in users:
            profile = getattr(u, 'profile', None)
            data.append({
                'id': u.id,
                'username': u.username,
                'nome': u.get_full_name(),
                'email': u.email,
                'telefone': profile.phone if profile else '',
                'cidade': profile.cidade if profile else '',
                'estado': profile.estado if profile else '',
                'admin': u.is_staff,
                'ativo': u.is_active,
                'cadastro': u.date_joined.isoformat(),
                'total_agendamentos': u.total_agendamentos,
                'concluidos': u.concluidos,
                'cancelados': u.cancelados,
                'gasto_total': str(u.gasto_total or 0),
            })
        return Response(data)


class AnalyticsLogsView(APIView):
    """
    GET /api/analytics/logs/
    Logs de ações dos usuários. Admin only.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        logs = ActionLog.objects.select_related('user').order_by('-timestamp')[:500]
        data = []
        for lg in logs:
            data.append({
                'id': lg.id,
                'usuario': lg.user.username if lg.user else None,
                'acao': lg.action,
                'acao_display': lg.get_action_display(),
                'descricao': lg.description,
                'ip': lg.ip_address,
                'caminho': lg.path,
                'metodo': lg.method,
                'timestamp': lg.timestamp.isoformat(),
            })
        return Response(data)
