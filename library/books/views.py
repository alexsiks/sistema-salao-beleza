from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Book, Category, Reservation, Comment, Rating, LibraryConfig
from .forms import BookForm, CommentForm, LibraryConfigForm
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
            user=request.user, book=book, status__in=['PENDING', 'ACTIVE', 'OVERDUE']
        ).first()
        ActionLog.log(user=request.user, action='BOOK_VIEW',
                      description=f'Visualizou: {book.title}', request=request)
    comment_form = CommentForm()
    config = LibraryConfig.get()
    return render(request, 'books/detail.html', {
        'book': book,
        'user_rating': user_rating,
        'user_reservation': user_reservation,
        'comment_form': comment_form,
        'star_range': range(1, 6),
        'config': config,
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
        messages.error(request, 'Não há exemplares disponíveis para empréstimo.')
        return redirect('books:detail', pk=pk)
    existing = Reservation.objects.filter(
        user=request.user, book=book, status__in=['PENDING', 'ACTIVE', 'OVERDUE']
    ).exists()
    if existing:
        messages.warning(request, 'Você já possui um empréstimo ativo para este livro.')
        return redirect('books:detail', pk=pk)

    config = LibraryConfig.get()
    reservation = Reservation.objects.create(
        user=request.user,
        book=book,
        status='PENDING',
        rental_price_snapshot=book.rental_price,
        fine_per_day_snapshot=config.fine_per_day,
    )
    book.available_copies -= 1
    book.save()
    ActionLog.log(user=request.user, action='BOOK_RESERVE',
                  description=f'Solicitou empréstimo: {book.title}', request=request,
                  extra_data={'book_id': book.id, 'rental_price': str(book.rental_price)})
    messages.success(request, f'Solicitação de empréstimo do livro "{book.title}" realizada! Aguarde a confirmação.')
    return redirect('books:my_reservations')


@login_required
def confirm_loan(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('books:list')
    reservation = get_object_or_404(Reservation, pk=pk, status='PENDING')
    if request.method == 'POST':
        reservation.confirm_loan()
        ActionLog.log(user=request.user, action='BOOK_RESERVE',
                      description=f'Empréstimo confirmado: {reservation.book.title} para {reservation.user.username}',
                      request=request)
        messages.success(request, f'Empréstimo confirmado! Devolução prevista: {reservation.due_date.strftime("%d/%m/%Y")}')
    return redirect('books:all_reservations')


@login_required
def return_book(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('books:list')
    reservation = get_object_or_404(Reservation, pk=pk)
    if reservation.status not in ('ACTIVE', 'OVERDUE', 'PENDING'):
        messages.error(request, 'Este empréstimo não pode ser registrado como devolvido.')
        return redirect('books:all_reservations')
    if request.method == 'POST':
        fine = reservation.process_return()
        ActionLog.log(user=request.user, action='RESERVATION_CANCEL',
                      description=f'Devolução registrada: {reservation.book.title} (multa: R$ {fine:.2f})',
                      request=request)
        if fine > 0:
            messages.warning(request, f'Devolução registrada com multa de R$ {fine:.2f} por {reservation.overdue_days} dia(s) de atraso.')
        else:
            messages.success(request, 'Devolução registrada com sucesso. Sem multa!')
    return redirect('books:all_reservations')


@login_required
def mark_fine_paid(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('books:list')
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        reservation.fine_paid = True
        reservation.save()
        messages.success(request, f'Multa de R$ {reservation.fine_amount:.2f} marcada como paga.')
    return redirect('books:all_reservations')


@login_required
def library_config(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('books:list')
    config = LibraryConfig.get()
    form = LibraryConfigForm(request.POST or None, instance=config)
    if request.method == 'POST' and form.is_valid():
        form.save()
        ActionLog.log(user=request.user, action='OTHER',
                      description='Configuração da biblioteca atualizada', request=request)
        messages.success(request, 'Configuração salva com sucesso!')
        return redirect('books:library_config')
    return render(request, 'books/library_config.html', {'form': form, 'config': config})


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
    for r in reservations:
        if r.status == 'ACTIVE' and r.is_overdue:
            r.status = 'OVERDUE'
            r.save(update_fields=['status'])
    return render(request, 'books/my_reservations.html', {'reservations': reservations})


@login_required
def cancel_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    if reservation.status not in ['PENDING']:
        messages.error(request, 'Apenas solicitações pendentes podem ser canceladas.')
        return redirect('books:my_reservations')
    if request.method == 'POST':
        reservation.status = 'CANCELLED'
        reservation.save()
        reservation.book.available_copies += 1
        reservation.book.save()
        ActionLog.log(user=request.user, action='RESERVATION_CANCEL',
                      description=f'Cancelou solicitação de: {reservation.book.title}',
                      request=request)
        messages.success(request, 'Solicitação cancelada com sucesso.')
    return redirect('books:my_reservations')


@login_required
def all_reservations(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('books:list')

    reservations = Reservation.objects.select_related('user', 'book').order_by('-reserved_at')

    for r in reservations:
        if r.status == 'ACTIVE' and r.is_overdue:
            r.status = 'OVERDUE'
            r.save(update_fields=['status'])

    status_filter = request.GET.get('status', '')
    if status_filter:
        reservations = reservations.filter(status=status_filter)

    from django.db.models import Sum
    from datetime import date as dt_date
    all_qs = Reservation.objects.all()
    pending_count = all_qs.filter(status='PENDING').count()
    active_count = all_qs.filter(status='ACTIVE').count()
    overdue_count = all_qs.filter(status__in=['ACTIVE', 'OVERDUE'], due_date__lt=dt_date.today()).count()
    fine_pending = all_qs.filter(status='RETURNED', fine_paid=False).aggregate(
        t=Sum('fine_amount'))['t'] or 0

    config = LibraryConfig.get()
    return render(request, 'books/all_reservations.html', {
        'reservations': reservations,
        'status_filter': status_filter,
        'status_choices': Reservation.STATUS_CHOICES,
        'config': config,
        'pending_count': pending_count,
        'active_count': active_count,
        'overdue_count': overdue_count,
        'fine_pending': f'{fine_pending:.2f}',
    })
