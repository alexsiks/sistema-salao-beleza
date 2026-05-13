from decimal import Decimal
from datetime import date, time, timedelta, datetime
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class SalonConfig(models.Model):
    salon_name = models.CharField('Nome do Salão', max_length=200, default='Espaço Beleza')
    phone = models.CharField('Telefone/WhatsApp', max_length=20, blank=True)
    address = models.TextField('Endereço', blank=True)
    open_time = models.TimeField('Abertura', default=time(9, 0))
    close_time = models.TimeField('Fechamento', default=time(18, 0))
    slot_minutes = models.PositiveIntegerField('Intervalo entre horários (min)', default=30)
    max_advance_days = models.PositiveIntegerField('Máximo de dias para agendar', default=30)
    cancellation_hours = models.PositiveIntegerField(
        'Antecedência mínima para cancelar (horas)', default=2
    )

    class Meta:
        verbose_name = 'Configuração do Salão'
        verbose_name_plural = 'Configuração do Salão'

    def __str__(self):
        return self.salon_name

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def available_slots(self, for_date, professional, service_duration):
        """Retorna lista de horários disponíveis para a data e profissional."""
        slots = []
        current = datetime.combine(for_date, self.open_time)
        end_limit = datetime.combine(for_date, self.close_time)
        step = timedelta(minutes=self.slot_minutes)
        duration = timedelta(minutes=service_duration)

        booked = set()
        appts = Appointment.objects.filter(
            professional=professional,
            date=for_date,
            status__in=['PENDING', 'CONFIRMED']
        )
        for a in appts:
            s = datetime.combine(for_date, a.start_time)
            e = datetime.combine(for_date, a.end_time)
            t = s
            while t < e:
                booked.add(t.time())
                t += step

        now = datetime.now()

        while current + duration <= end_limit:
            slot_end = current + duration
            slot_times = set()
            t = current
            while t < slot_end:
                slot_times.add(t.time())
                t += step

            if not slot_times & booked and current > now:
                slots.append(current.time())
            current += step

        return slots


class ServiceCategory(models.Model):
    name = models.CharField('Categoria', max_length=100, unique=True)
    icon = models.CharField('Ícone Bootstrap', max_length=50, default='bi-scissors')
    description = models.TextField('Descrição', blank=True)

    class Meta:
        verbose_name = 'Categoria de Serviço'
        verbose_name_plural = 'Categorias de Serviços'
        ordering = ['name']

    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField('Nome do Serviço', max_length=200)
    description = models.TextField('Descrição')
    duration_minutes = models.PositiveIntegerField(
        'Duração (minutos)', default=60,
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        'Preço (R$)', max_digits=8, decimal_places=2,
        default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))]
    )
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='services', verbose_name='Categoria'
    )
    image = models.ImageField('Foto', upload_to='servicos/', blank=True, null=True)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} — {self.duration_minutes}min — R$ {self.price}'

    @property
    def duration_display(self):
        h = self.duration_minutes // 60
        m = self.duration_minutes % 60
        if h and m:
            return f'{h}h{m:02d}min'
        elif h:
            return f'{h}h'
        return f'{m}min'


class Professional(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='professional', verbose_name='Usuário')
    bio = models.TextField('Sobre', blank=True)
    photo = models.ImageField('Foto', upload_to='profissionais/', blank=True, null=True)
    services = models.ManyToManyField(Service, blank=True,
                                      related_name='professionals', verbose_name='Serviços')
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Profissional'
        verbose_name_plural = 'Profissionais'

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def upcoming_appointments(self):
        return self.appointments.filter(
            date__gte=date.today(),
            status__in=['PENDING', 'CONFIRMED']
        ).count()


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING',   'Pendente'),
        ('CONFIRMED', 'Confirmado'),
        ('CANCELLED', 'Cancelado'),
        ('COMPLETED', 'Concluído'),
        ('NO_SHOW',   'Não Compareceu'),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='appointments', verbose_name='Cliente')
    professional = models.ForeignKey(Professional, on_delete=models.SET_NULL,
                                     null=True, blank=True,
                                     related_name='appointments', verbose_name='Profissional')
    service = models.ForeignKey(Service, on_delete=models.PROTECT,
                                related_name='appointments', verbose_name='Serviço')
    date = models.DateField('Data')
    start_time = models.TimeField('Horário de Início')
    end_time = models.TimeField('Horário de Término')
    status = models.CharField('Status', max_length=15,
                              choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField('Observações do Cliente', blank=True)
    internal_notes = models.TextField('Observações Internas', blank=True)
    price_snapshot = models.DecimalField(
        'Preço (R$)', max_digits=8, decimal_places=2, default=Decimal('0.00')
    )
    duration_snapshot = models.PositiveIntegerField('Duração (min)', default=60)
    cancel_reason = models.TextField('Motivo do Cancelamento', blank=True)
    created_at = models.DateTimeField('Agendado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
        ordering = ['date', 'start_time']

    def __str__(self):
        return (f'{self.client.get_full_name() or self.client.username} — '
                f'{self.service.name} — {self.date:%d/%m/%Y} {self.start_time:%H:%M}')

    @property
    def is_upcoming(self):
        return self.date >= date.today() and self.status in ('PENDING', 'CONFIRMED')

    @property
    def is_past(self):
        return self.date < date.today()

    @property
    def datetime_start(self):
        return datetime.combine(self.date, self.start_time)

    def can_cancel(self, config=None):
        if config is None:
            config = SalonConfig.get()
        if self.status not in ('PENDING', 'CONFIRMED'):
            return False
        deadline = self.datetime_start - timedelta(hours=config.cancellation_hours)
        return datetime.now() <= deadline
