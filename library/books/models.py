from decimal import Decimal
from datetime import date, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg


class LibraryConfig(models.Model):
    fine_per_day = models.DecimalField(
        'Multa por Dia de Atraso (R$)', max_digits=6, decimal_places=2,
        default=Decimal('1.00'), validators=[MinValueValidator(Decimal('0.00'))]
    )
    max_loan_days = models.PositiveIntegerField(
        'Prazo Máximo de Empréstimo (dias)', default=14
    )

    class Meta:
        verbose_name = 'Configuração da Biblioteca'
        verbose_name_plural = 'Configuração da Biblioteca'

    def __str__(self):
        return f'Prazo: {self.max_loan_days} dias | Multa: R$ {self.fine_per_day}/dia'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField('Nome', max_length=100, unique=True)
    description = models.TextField('Descrição', blank=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField('Título', max_length=300)
    author = models.CharField('Autor', max_length=200)
    isbn = models.CharField('ISBN', max_length=13, blank=True)
    publisher = models.CharField('Editora', max_length=200, blank=True)
    year = models.PositiveIntegerField('Ano de Publicação', null=True, blank=True)
    description = models.TextField('Descrição')
    cover_image = models.ImageField('Capa', upload_to='livros/', blank=True, null=True)
    categories = models.ManyToManyField(Category, blank=True, verbose_name='Categorias')
    total_copies = models.PositiveIntegerField('Total de Exemplares', default=1)
    available_copies = models.PositiveIntegerField('Exemplares Disponíveis', default=1)
    rental_price = models.DecimalField(
        'Valor do Empréstimo (R$)', max_digits=8, decimal_places=2,
        default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='created_books', verbose_name='Cadastrado por')
    created_at = models.DateTimeField('Cadastrado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Livro'
        verbose_name_plural = 'Livros'
        ordering = ['title']

    def __str__(self):
        return f'{self.title} — {self.author}'

    @property
    def average_rating(self):
        avg = self.ratings.aggregate(avg=Avg('score'))['avg']
        return round(avg, 1) if avg else None

    @property
    def is_available(self):
        return self.available_copies > 0

    @property
    def rating_count(self):
        return self.ratings.count()


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('PENDING',   'Pendente'),
        ('ACTIVE',    'Em Empréstimo'),
        ('OVERDUE',   'Em Atraso'),
        ('RETURNED',  'Devolvido'),
        ('CANCELLED', 'Cancelado'),
        ('EXPIRED',   'Expirado'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='reservations', verbose_name='Usuário')
    book = models.ForeignKey(Book, on_delete=models.CASCADE,
                             related_name='reservations', verbose_name='Livro')
    status = models.CharField('Status', max_length=15, choices=STATUS_CHOICES, default='PENDING')

    reserved_at = models.DateTimeField('Reservado em', auto_now_add=True)
    loan_date = models.DateField('Data do Empréstimo', null=True, blank=True)
    due_date = models.DateField('Data de Devolução Prevista', null=True, blank=True)
    returned_at = models.DateTimeField('Devolvido em', null=True, blank=True)

    rental_price_snapshot = models.DecimalField(
        'Valor do Empréstimo (R$)', max_digits=8, decimal_places=2,
        default=Decimal('0.00')
    )
    fine_per_day_snapshot = models.DecimalField(
        'Multa/Dia na época (R$)', max_digits=6, decimal_places=2,
        default=Decimal('0.00')
    )
    fine_amount = models.DecimalField(
        'Valor da Multa (R$)', max_digits=10, decimal_places=2,
        default=Decimal('0.00')
    )
    fine_paid = models.BooleanField('Multa Paga', default=False)
    notes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Empréstimo'
        verbose_name_plural = 'Empréstimos'
        ordering = ['-reserved_at']

    def __str__(self):
        return f'{self.user.username} — {self.book.title} ({self.get_status_display()})'

    @property
    def is_overdue(self):
        if self.status in ('RETURNED', 'CANCELLED', 'EXPIRED'):
            return False
        if self.due_date and date.today() > self.due_date:
            return True
        return False

    @property
    def overdue_days(self):
        if not self.due_date:
            return 0
        if self.returned_at:
            ref = self.returned_at.date()
        else:
            ref = date.today()
        delta = (ref - self.due_date).days
        return max(0, delta)

    @property
    def calculated_fine(self):
        return Decimal(str(self.overdue_days)) * self.fine_per_day_snapshot

    @property
    def total_amount(self):
        return self.rental_price_snapshot + self.fine_amount

    def confirm_loan(self):
        config = LibraryConfig.get()
        self.loan_date = date.today()
        self.due_date = date.today() + timedelta(days=config.max_loan_days)
        self.status = 'ACTIVE'
        self.save()

    def process_return(self):
        from django.utils import timezone
        self.returned_at = timezone.now()
        self.fine_amount = self.calculated_fine
        self.status = 'RETURNED'
        self.book.available_copies += 1
        self.book.save()
        self.save()
        return self.fine_amount


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='comments', verbose_name='Usuário')
    book = models.ForeignKey(Book, on_delete=models.CASCADE,
                             related_name='comments', verbose_name='Livro')
    content = models.TextField('Comentário')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    is_visible = models.BooleanField('Visível', default=True)

    class Meta:
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} em "{self.book.title}"'


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='ratings', verbose_name='Usuário')
    book = models.ForeignKey(Book, on_delete=models.CASCADE,
                             related_name='ratings', verbose_name='Livro')
    score = models.PositiveSmallIntegerField(
        'Nota', validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField('Avaliado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        unique_together = ('user', 'book')

    def __str__(self):
        return f'{self.user.username} — {self.book.title}: {self.score}/5'
