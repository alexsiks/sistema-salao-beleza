from datetime import date, datetime, timedelta
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.contrib.auth.models import User
from .models import Service, ServiceCategory, Professional, Appointment, SalonConfig, ClosedDate, WEEKDAY_CHOICES
from .forms import ServiceForm, SalonConfigForm, AppointmentBookingForm, ClosedDateForm
from accounts.models import ActionLog


def service_list(request):
    config = SalonConfig.get()
    services = Service.objects.filter(is_active=True).select_related('category')
    categories = ServiceCategory.objects.all()

    q = request.GET.get('q', '')
    cat_id = request.GET.get('category', '')
    if q:
        services = services.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if cat_id:
        services = services.filter(category_id=cat_id)

    return render(request, 'servicos/list.html', {
        'services': services,
        'categories': categories,
        'q': q,
        'cat_id': cat_id,
        'config': config,
    })


def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk, is_active=True)
    professionals = service.professionals.filter(is_active=True)
    config = SalonConfig.get()
    return render(request, 'servicos/detail.html', {
        'service': service,
        'professionals': professionals,
        'config': config,
    })


@login_required
def book_appointment(request, pk):
    service = get_object_or_404(Service, pk=pk, is_active=True)
    config = SalonConfig.get()

    if request.method == 'POST':
        professional_id = request.POST.get('professional') or None
        appt_date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')

        if not appt_date_str or not start_time_str:
            messages.error(request, 'Selecione a data e o horário.')
            return redirect('servicos:book', pk=pk)

        appt_date = datetime.strptime(appt_date_str, '%Y-%m-%d').date()

        if not config.is_open_on(appt_date):
            messages.error(request, 'O salão não funciona nesta data.')
            return redirect('servicos:book', pk=pk)

        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_dt = datetime.combine(appt_date, start_time) + timedelta(minutes=service.duration_minutes)
        end_time = end_dt.time()

        professional = None
        if professional_id:
            professional = get_object_or_404(Professional, pk=professional_id, is_active=True)
        else:
            profs = service.professionals.filter(is_active=True)
            for p in profs:
                slots = config.available_slots(appt_date, p, service.duration_minutes)
                if start_time in slots:
                    professional = p
                    break
            if not professional and profs.exists():
                professional = profs.first()

        if professional:
            conflict = Appointment.objects.filter(
                professional=professional,
                date=appt_date,
                status__in=['PENDING', 'CONFIRMED'],
            ).filter(
                Q(start_time__lt=end_time, end_time__gt=start_time)
            ).exists()
            if conflict:
                messages.error(request, 'Este horário já está ocupado. Escolha outro.')
                return redirect('servicos:book', pk=pk)

        appt = Appointment.objects.create(
            client=request.user,
            professional=professional,
            service=service,
            date=appt_date,
            start_time=start_time,
            end_time=end_time,
            notes=request.POST.get('notes', ''),
            price_snapshot=service.price,
            duration_snapshot=service.duration_minutes,
        )
        ActionLog.log(user=request.user, action='OTHER',
                      description=f'Agendamento criado: {service.name} em {appt_date}',
                      request=request)
        messages.success(request, f'Agendamento de "{service.name}" realizado com sucesso!')
        return redirect('servicos:my_appointments')

    professionals = service.professionals.filter(is_active=True)
    max_date = date.today() + timedelta(days=config.max_advance_days)
    return render(request, 'servicos/book.html', {
        'service': service,
        'professionals': professionals,
        'config': config,
        'min_date': date.today().strftime('%Y-%m-%d'),
        'max_date': max_date.strftime('%Y-%m-%d'),
    })


def available_slots_api(request):
    """AJAX endpoint: returns available time slots."""
    service_id = request.GET.get('service')
    professional_id = request.GET.get('professional')
    date_str = request.GET.get('date')

    if not service_id or not date_str:
        return JsonResponse({'slots': [], 'error': 'Parâmetros obrigatórios: service, date'})

    try:
        appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'slots': [], 'error': 'Data inválida'})

    if appt_date < date.today():
        return JsonResponse({'slots': []})

    config = SalonConfig.get()

    if not config.is_open_on(appt_date):
        return JsonResponse({'slots': [], 'closed': True, 'message': 'O salão não funciona nesta data.'})

    try:
        service = Service.objects.get(pk=service_id, is_active=True)
    except Service.DoesNotExist:
        return JsonResponse({'slots': [], 'error': 'Serviço não encontrado'})

    if professional_id:
        try:
            professional = Professional.objects.get(pk=professional_id, is_active=True)
        except Professional.DoesNotExist:
            return JsonResponse({'slots': []})
        slots = config.available_slots(appt_date, professional, service.duration_minutes)
    else:
        profs = service.professionals.filter(is_active=True)
        all_slots = set()
        for p in profs:
            s = config.available_slots(appt_date, p, service.duration_minutes)
            all_slots.update(s)
        slots = sorted(all_slots)

    return JsonResponse({'slots': [s.strftime('%H:%M') for s in slots]})


@login_required
def my_appointments(request):
    upcoming = Appointment.objects.filter(
        client=request.user,
        date__gte=date.today(),
        status__in=['PENDING', 'CONFIRMED']
    ).select_related('service', 'professional__user').order_by('date', 'start_time')

    past = Appointment.objects.filter(
        client=request.user,
    ).exclude(
        date__gte=date.today(), status__in=['PENDING', 'CONFIRMED']
    ).select_related('service', 'professional__user').order_by('-date', '-start_time')[:20]

    config = SalonConfig.get()
    return render(request, 'servicos/my_appointments.html', {
        'upcoming': [a for a in upcoming if True],
        'past': past,
        'config': config,
    })


@login_required
def cancel_appointment(request, pk):
    appt = get_object_or_404(Appointment, pk=pk, client=request.user)
    config = SalonConfig.get()
    if not appt.can_cancel(config):
        messages.error(request, 'Não é possível cancelar este agendamento.')
        return redirect('servicos:my_appointments')
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        appt.status = 'CANCELLED'
        appt.cancel_reason = reason
        appt.save()
        ActionLog.log(user=request.user, action='OTHER',
                      description=f'Agendamento cancelado: {appt.service.name}',
                      request=request)
        messages.success(request, 'Agendamento cancelado.')
    return redirect('servicos:my_appointments')


# ── Admin views ─────────────────────────────────────────────────────────────

@login_required
def all_appointments(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('servicos:list')

    appts = Appointment.objects.select_related(
        'client', 'professional__user', 'service'
    ).order_by('date', 'start_time')

    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    prof_filter = request.GET.get('professional', '')

    if status_filter:
        appts = appts.filter(status=status_filter)
    if date_filter:
        appts = appts.filter(date=date_filter)
    if prof_filter:
        appts = appts.filter(professional_id=prof_filter)

    professionals = Professional.objects.filter(is_active=True).select_related('user')
    config = SalonConfig.get()

    today_count = Appointment.objects.filter(date=date.today()).count()
    pending_count = Appointment.objects.filter(status='PENDING').count()
    confirmed_count = Appointment.objects.filter(
        date__gte=date.today(), status='CONFIRMED').count()

    return render(request, 'servicos/all_reservations.html', {
        'appointments': appts,
        'professionals': professionals,
        'status_choices': Appointment.STATUS_CHOICES,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'prof_filter': prof_filter,
        'config': config,
        'today_count': today_count,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
    })


@login_required
def confirm_appointment(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('servicos:list')
    appt = get_object_or_404(Appointment, pk=pk, status='PENDING')
    if request.method == 'POST':
        appt.status = 'CONFIRMED'
        appt.internal_notes = request.POST.get('internal_notes', appt.internal_notes)
        appt.save()
        ActionLog.log(user=request.user, action='OTHER',
                      description=f'Agendamento confirmado: {appt}', request=request)
        messages.success(request, 'Agendamento confirmado!')
    return redirect('servicos:all_appointments')


@login_required
def reject_appointment(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('servicos:list')
    appt = get_object_or_404(Appointment, pk=pk)
    if appt.status not in ('PENDING', 'CONFIRMED'):
        messages.error(request, 'Este agendamento não pode ser cancelado.')
        return redirect('servicos:all_appointments')
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        appt.status = 'CANCELLED'
        appt.cancel_reason = reason
        appt.save()
        ActionLog.log(user=request.user, action='OTHER',
                      description=f'Agendamento cancelado pelo salão: {appt}',
                      request=request)
        messages.warning(request, 'Agendamento cancelado.')
    return redirect('servicos:all_appointments')


@login_required
def complete_appointment(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('servicos:list')
    appt = get_object_or_404(Appointment, pk=pk, status='CONFIRMED')
    if request.method == 'POST':
        appt.status = 'COMPLETED'
        appt.internal_notes = request.POST.get('internal_notes', appt.internal_notes)
        appt.save()
        ActionLog.log(user=request.user, action='OTHER',
                      description=f'Serviço concluído: {appt}', request=request)
        messages.success(request, 'Serviço marcado como concluído!')
    return redirect('servicos:all_appointments')


@login_required
def no_show_appointment(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('servicos:list')
    appt = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appt.status = 'NO_SHOW'
        appt.save()
        messages.warning(request, 'Agendamento marcado como não compareceu.')
    return redirect('servicos:all_appointments')


@login_required
def service_create(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('servicos:list')
    config = SalonConfig.get()
    form = ServiceForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        service = form.save()
        messages.success(request, f'Serviço "{service.name}" cadastrado!')
        return redirect('servicos:list')
    return render(request, 'servicos/service_form.html', {'form': form, 'action': 'Cadastrar', 'config': config})


@login_required
def service_edit(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('servicos:list')
    service = get_object_or_404(Service, pk=pk)
    config = SalonConfig.get()
    form = ServiceForm(request.POST or None, request.FILES or None, instance=service)
    if request.method == 'POST' and form.is_valid():
        instance = form.save(commit=False)
        if not request.FILES.get('image') and not request.POST.get('image_clear'):
            instance.image = service.image
        elif request.POST.get('image_clear'):
            instance.image = None
        instance.save()
        messages.success(request, f'Serviço "{service.name}" atualizado!')
        return redirect('servicos:list')
    return render(request, 'servicos/service_form.html',
                  {'form': form, 'service': service, 'action': 'Editar', 'config': config})


@login_required
def service_delete(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('servicos:list')
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        service.is_active = False
        service.save()
        messages.success(request, f'Serviço "{service.name}" desativado.')
        return redirect('servicos:list')
    return render(request, 'servicos/confirm_delete.html', {'service': service})


@login_required
def professionals_list(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('servicos:list')
    professionals = Professional.objects.filter(
        is_active=True).select_related('user').prefetch_related('services')
    config = SalonConfig.get()
    return render(request, 'servicos/professionals.html', {'professionals': professionals, 'config': config})


@login_required
def dashboard_24h(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('servicos:list')

    config = SalonConfig.get()
    now = datetime.now()
    since = now - timedelta(hours=24)
    today = date.today()

    # Appointments created in last 24h
    appts_24h = Appointment.objects.filter(
        created_at__gte=since
    ).select_related('client', 'professional__user', 'service').order_by('-created_at')

    # Appointments scheduled for today
    todays_appts = Appointment.objects.filter(
        date=today
    ).select_related('client', 'professional__user', 'service').order_by('start_time')

    # Status counts (last 24h created)
    status_counts = {s: 0 for s, _ in Appointment.STATUS_CHOICES}
    for a in appts_24h:
        status_counts[a.status] = status_counts.get(a.status, 0) + 1

    # Revenue from completed appointments today
    revenue_today = todays_appts.filter(status='COMPLETED').aggregate(
        total=Sum('price_snapshot')
    )['total'] or Decimal('0.00')

    # Revenue from completed in last 24h (created)
    revenue_24h = appts_24h.filter(status='COMPLETED').aggregate(
        total=Sum('price_snapshot')
    )['total'] or Decimal('0.00')

    # Upcoming appointments today (pending/confirmed, not yet started)
    upcoming_today = [a for a in todays_appts if a.status in ('PENDING', 'CONFIRMED')]

    # New users in last 24h
    new_users = User.objects.filter(date_joined__gte=since).order_by('-date_joined')

    # Top services in last 24h
    top_services = (
        Appointment.objects.filter(created_at__gte=since)
        .values('service__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    # Professional performance today
    prof_stats = []
    professionals = Professional.objects.filter(is_active=True).select_related('user')
    for p in professionals:
        pday = todays_appts.filter(professional=p)
        prof_stats.append({
            'professional': p,
            'total': pday.count(),
            'completed': pday.filter(status='COMPLETED').count(),
            'pending': pday.filter(status='PENDING').count(),
            'confirmed': pday.filter(status='CONFIRMED').count(),
            'revenue': pday.filter(status='COMPLETED').aggregate(
                t=Sum('price_snapshot'))['t'] or Decimal('0.00'),
        })
    prof_stats.sort(key=lambda x: x['total'], reverse=True)

    # Recent action logs last 24h
    recent_logs = ActionLog.objects.filter(
        timestamp__gte=since
    ).select_related('user').order_by('-timestamp')[:30]

    # Today totals for the top cards
    today_total = todays_appts.count()
    today_confirmed = todays_appts.filter(status='CONFIRMED').count()
    today_pending = todays_appts.filter(status='PENDING').count()
    today_completed = todays_appts.filter(status='COMPLETED').count()
    today_cancelled = todays_appts.filter(status='CANCELLED').count()

    return render(request, 'servicos/dashboard_24h.html', {
        'config': config,
        'now': now,
        'since': since,
        'appts_24h': appts_24h,
        'todays_appts': todays_appts,
        'upcoming_today': upcoming_today,
        'status_counts': status_counts,
        'revenue_today': revenue_today,
        'revenue_24h': revenue_24h,
        'new_users': new_users,
        'top_services': top_services,
        'prof_stats': prof_stats,
        'recent_logs': recent_logs,
        'today_total': today_total,
        'today_confirmed': today_confirmed,
        'today_pending': today_pending,
        'today_completed': today_completed,
        'today_cancelled': today_cancelled,
    })


@login_required
def salon_config(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('servicos:list')
    config = SalonConfig.get()
    form = SalonConfigForm(request.POST or None, instance=config)
    closed_form = ClosedDateForm()
    closed_dates = ClosedDate.objects.all()

    if request.method == 'POST':
        action = request.POST.get('_action', 'config')
        if action == 'add_closed':
            closed_form = ClosedDateForm(request.POST)
            if closed_form.is_valid():
                closed_form.save()
                messages.success(request, 'Data fechada adicionada.')
                return redirect('servicos:salon_config')
        elif action == 'delete_closed':
            cd_pk = request.POST.get('closed_date_id')
            ClosedDate.objects.filter(pk=cd_pk).delete()
            messages.success(request, 'Data removida.')
            return redirect('servicos:salon_config')
        else:
            if form.is_valid():
                form.save()
                messages.success(request, 'Configurações salvas!')
                return redirect('servicos:salon_config')

    return render(request, 'servicos/library_config.html', {
        'form': form,
        'config': config,
        'closed_form': closed_form,
        'closed_dates': closed_dates,
        'weekday_choices': WEEKDAY_CHOICES,
    })
