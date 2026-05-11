from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Book, Category, Reservation, Comment, Rating
from .forms import BookForm, CommentForm
from accounts.models import ActionLog


def book_list(request):
    books = Book.objects.prefetch_related('categories', 'ratings').order_by('title')
    q = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    available = request.GET.get('available', '')

    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(description__icontains=q))
    if category_id:
        books = books.filter(categories__id=category_id)
    if available == '1':
        books = books.filter(available_copies__gt=0)

    categories = Category.objects.all()
    return render(request, 'books/list.html', {
        'books': books, 'categories': categories,
        'q': q, 'category_id': category_id, 'available': available
    })


def book_detail(request, pk):
    book = get_object_or_404(Book.objects.prefetch_related('categories', 'comments__user', 'ratings'), pk=pk)
    user_rating = None
    user_reservation = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(user=request.user, book=book).first()
        user_reservation = Reservation.objects.filter(
            user=request.user, book=book, status__in=['PENDING', 'ACTIVE']
        ).first()
        ActionLog.log(user=request.user, action='BOOK_VIEW',
                      description=f'Visualizou: {book.title}', request=request)
    comment_form = CommentForm()
    return render(request, 'books/detail.html', {
        'book': book,
        'user_rating': user_rating,
        'user_reservation': user_reservation,
        'comment_form': comment_form,
        'star_range': range(1, 6),
    })


@login_required
def book_create(request):
    if not request.user.is_staff:
        messages.error(request, 'Somente administradores podem cadastrar livros.')
        return redirect('books:list')
    form = BookForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        book = form.save(commit=False)
        book.created_by = request.user
        book.available_copies = book.total_copies
        book.save()
        form.save_m2m()
        ActionLog.log(user=request.user, action='BOOK_CREATE',
                      description=f'Livro cadastrado: {book.title}', request=request,
                      extra_data={'book_id': book.id, 'title': book.title})
        messages.success(request, f'Livro "{book.title}" cadastrado com sucesso!')
        return redirect('books:detail', pk=book.pk)
    return render(request, 'books/form.html', {'form': form, 'action': 'Cadastrar'})


@login_required
def book_edit(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Somente administradores podem editar livros.')
        return redirect('books:list')
    book = get_object_or_404(Book, pk=pk)
    form = BookForm(request.POST or None, request.FILES or None, instance=book)
    if request.method == 'POST' and form.is_valid():
        form.save()
        ActionLog.log(user=request.user, action='BOOK_UPDATE',
                      description=f'Livro editado: {book.title}', request=request)
        messages.success(request, f'Livro "{book.title}" atualizado!')
        return redirect('books:detail', pk=book.pk)
    return render(request, 'books/form.html', {'form': form, 'book': book, 'action': 'Editar'})


@login_required
def book_delete(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Somente administradores podem excluir livros.')
        return redirect('books:list')
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        title = book.title
        ActionLog.log(user=request.user, action='BOOK_DELETE',
                      description=f'Livro excluído: {title}', request=request)
        book.delete()
        messages.success(request, f'Livro "{title}" excluído.')
        return redirect('books:list')
    return render(request, 'books/confirm_delete.html', {'book': book})


@login_required
def book_reserve(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if book.available_copies <= 0:
        messages.error(request, 'Não há exemplares disponíveis para reserva.')
        return redirect('books:detail', pk=pk)
    existing = Reservation.objects.filter(
        user=request.user, book=book, status__in=['PENDING', 'ACTIVE']
    ).exists()
    if existing:
        messages.warning(request, 'Você já possui uma reserva ativa para este livro.')
        return redirect('books:detail', pk=pk)
    Reservation.objects.create(user=request.user, book=book, status='PENDING')
    book.available_copies -= 1
    book.save()
    ActionLog.log(user=request.user, action='BOOK_RESERVE',
                  description=f'Reservou: {book.title}', request=request,
                  extra_data={'book_id': book.id})
    messages.success(request, f'Livro "{book.title}" reservado com sucesso!')
    return redirect('books:my_reservations')


@login_required
def add_comment(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.book = book
            comment.save()
            ActionLog.log(user=request.user, action='COMMENT_ADD',
                          description=f'Comentou em: {book.title}', request=request)
            messages.success(request, 'Comentário adicionado!')
    return redirect('books:detail', pk=pk)


@login_required
def add_rating(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        score = request.POST.get('score')
        try:
            score = int(score)
            if 1 <= score <= 5:
                rating, created = Rating.objects.update_or_create(
                    user=request.user, book=book,
                    defaults={'score': score}
                )
                ActionLog.log(user=request.user, action='RATING_ADD',
                              description=f'Avaliou {book.title} com {score}/5', request=request)
                messages.success(request, f'Avaliação de {score}/5 registrada!')
            else:
                messages.error(request, 'Nota inválida.')
        except (ValueError, TypeError):
            messages.error(request, 'Nota inválida.')
    return redirect('books:detail', pk=pk)


@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(
        user=request.user
    ).select_related('book').order_by('-reserved_at')
    return render(request, 'books/my_reservations.html', {'reservations': reservations})


@login_required
def cancel_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    if reservation.status not in ['PENDING', 'ACTIVE']:
        messages.error(request, 'Esta reserva não pode ser cancelada.')
        return redirect('books:my_reservations')
    if request.method == 'POST':
        reservation.status = 'CANCELLED'
        reservation.save()
        reservation.book.available_copies += 1
        reservation.book.save()
        ActionLog.log(user=request.user, action='RESERVATION_CANCEL',
                      description=f'Cancelou reserva de: {reservation.book.title}',
                      request=request)
        messages.success(request, 'Reserva cancelada com sucesso.')
    return redirect('books:my_reservations')


@login_required
def all_reservations(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('books:list')
    reservations = Reservation.objects.select_related('user', 'book').order_by('-reserved_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        reservations = reservations.filter(status=status_filter)
    return render(request, 'books/all_reservations.html', {
        'reservations': reservations,
        'status_filter': status_filter,
        'status_choices': Reservation.STATUS_CHOICES,
    })
