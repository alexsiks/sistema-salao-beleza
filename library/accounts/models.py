from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
        ('N', 'Prefiro não informar'),
    ]

    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    gender      = models.CharField('Sexo', max_length=1, choices=GENDER_CHOICES, blank=True)
    birth_date  = models.DateField('Data de Nascimento', null=True, blank=True)
    phone       = models.CharField('Telefone', max_length=20, blank=True)
    cep         = models.CharField('CEP', max_length=9, blank=True)
    logradouro  = models.CharField('Logradouro', max_length=200, blank=True)
    bairro      = models.CharField('Bairro', max_length=100, blank=True)
    cidade      = models.CharField('Cidade', max_length=100, blank=True)
    estado      = models.CharField('Estado', max_length=2, blank=True)
    complemento = models.CharField('Complemento', max_length=100, blank=True)
    numero      = models.CharField('Número', max_length=10, blank=True)
    bio         = models.TextField('Biografia', blank=True)
    created_at  = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at  = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name        = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f'Perfil de {self.user.get_full_name() or self.user.username}'

    @property
    def age(self):
        if not self.birth_date:
            return None
        from datetime import date
        today = date.today()
        b = self.birth_date
        return today.year - b.year - ((today.month, today.day) < (b.month, b.day))

    @property
    def full_address(self):
        parts = []
        for attr in ('logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado'):
            v = getattr(self, attr)
            if v:
                parts.append(v)
        if self.cep:
            parts.append(f'CEP: {self.cep}')
        return ', '.join(parts)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


class ActionLog(models.Model):
    ACTION_TYPES = [
        ('LOGIN',               'Login'),
        ('LOGOUT',              'Logout'),
        ('REGISTER',            'Cadastro'),
        ('PROFILE_UPDATE',      'Atualização de Perfil'),
        ('BOOK_VIEW',           'Visualização de Livro'),
        ('BOOK_RESERVE',        'Reserva de Livro'),
        ('RESERVATION_CANCEL',  'Cancelamento de Reserva'),
        ('COMMENT_ADD',         'Adição de Comentário'),
        ('RATING_ADD',          'Avaliação de Livro'),
        ('BOOK_CREATE',         'Criação de Livro'),
        ('BOOK_UPDATE',         'Atualização de Livro'),
        ('BOOK_DELETE',         'Exclusão de Livro'),
        ('USER_CREATE',         'Criação de Usuário'),
        ('USER_UPDATE',         'Atualização de Usuário'),
        ('USER_DELETE',         'Exclusão de Usuário'),
        ('TOKEN_REGENERATE',    'Regeneração de Token'),
        ('OTHER',               'Outro'),
    ]

    user       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='action_logs', verbose_name='Usuário')
    action     = models.CharField('Ação', max_length=30, choices=ACTION_TYPES)
    description= models.TextField('Descrição', blank=True)
    ip_address = models.GenericIPAddressField('Endereço IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    path       = models.CharField('Caminho', max_length=500, blank=True)
    method     = models.CharField('Método HTTP', max_length=10, blank=True)
    timestamp  = models.DateTimeField('Data/Hora', auto_now_add=True)
    extra_data = models.JSONField('Dados Extras', default=dict, blank=True)

    class Meta:
        verbose_name        = 'Log de Ação'
        verbose_name_plural = 'Logs de Ações'
        ordering            = ['-timestamp']

    def __str__(self):
        username = self.user.username if self.user else 'Anônimo'
        return f'{username} — {self.get_action_display()} em {self.timestamp.strftime("%d/%m/%Y %H:%M")}'

    @classmethod
    def log(cls, user=None, action='OTHER', description='', request=None, extra_data=None):
        entry = cls(user=user, action=action, description=description, extra_data=extra_data or {})
        if request:
            entry.ip_address = cls._get_client_ip(request)
            entry.user_agent = request.META.get('HTTP_USER_AGENT', '')
            entry.path       = request.path
            entry.method     = request.method
        entry.save()
        return entry

    @staticmethod
    def _get_client_ip(request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
