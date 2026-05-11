from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg


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
    cover_image = models.ImageField('Capa', upload_to='books/', blank=True, null=True)
    categories = models.ManyToManyField(Category, blank=True, verbose_name='Categorias')
    total_copies = models.PositiveIntegerField('Total de Exemplares', default=1)
    available_copies = models.PositiveIntegerField('Exemplares Disponíveis', default=1)
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
        ('PENDING', 'Pendente'),
        ('ACTIVE', 'Ativa'),
        ('RETURNED', 'Devolvido'),
        ('CANCELLED', 'Cancelada'),
        ('EXPIRED', 'Expirada'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='reservations', verbose_name='Usuário')
    book = models.ForeignKey(Book, on_delete=models.CASCADE,
                             related_name='reservations', verbose_name='Livro')
    status = models.CharField('Status', max_length=15, choices=STATUS_CHOICES, default='PENDING')
    reserved_at = models.DateTimeField('Reservado em', auto_now_add=True)
    pickup_deadline = models.DateTimeField('Prazo para Retirada', null=True, blank=True)
    returned_at = models.DateTimeField('Devolvido em', null=True, blank=True)
    notes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-reserved_at']

    def __str__(self):
        return f'{self.user.username} — {self.book.title} ({self.get_status_display()})'


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
