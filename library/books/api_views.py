from decimal import Decimal
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Book, Category, Reservation, Comment, Rating, LibraryConfig
from .serializers import (BookListSerializer, BookDetailSerializer,
                           ReservationSerializer, CommentSerializer,
                           RatingSerializer, CategorySerializer,
                           LibraryConfigSerializer)
from accounts.models import ActionLog


class LibraryConfigAPIView(APIView):
    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get(self, request):
        config = LibraryConfig.get()
        return Response(LibraryConfigSerializer(config).data)

    def put(self, request):
        config = LibraryConfig.get()
        serializer = LibraryConfigSerializer(config, data=request.data)
        if serializer.is_valid():
            serializer.save()
            ActionLog.log(user=request.user, action='OTHER',
                          description='Configuração da biblioteca atualizada via API',
                          request=request)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        config = LibraryConfig.get()
        serializer = LibraryConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            ActionLog.log(user=request.user, action='OTHER',
                          description='Configuração da biblioteca atualizada via API',
                          request=request)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookListAPIView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BookDetailSerializer
        return BookListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = Book.objects.prefetch_related('categories', 'ratings').order_by('title')
        q = self.request.query_params.get('q')
        category = self.request.query_params.get('category')
        available = self.request.query_params.get('available')
        if q:
            from django.db.models import Q
            qs = qs.filter(Q(title__icontains=q) | Q(author__icontains=q))
        if category:
            qs = qs.filter(categories__id=category)
        if available == '1':
            qs = qs.filter(available_copies__gt=0)
        return qs

    def perform_create(self, serializer):
        book = serializer.save(created_by=self.request.user,
                               available_copies=serializer.validated_data.get('total_copies', 1))
        ActionLog.log(user=self.request.user, action='BOOK_CREATE',
                      description=f'Livro criado via API: {book.title}', request=self.request)


class BookDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.prefetch_related('categories', 'comments__user', 'ratings').all()
    serializer_class = BookDetailSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class ReserveBookAPIView(APIView):
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        if book.available_copies <= 0:
            return Response({'error': 'Sem exemplares disponíveis.'}, status=status.HTTP_400_BAD_REQUEST)
        existing = Reservation.objects.filter(
            user=request.user, book=book, status__in=['PENDING', 'ACTIVE', 'OVERDUE']
        ).exists()
        if existing:
            return Response({'error': 'Você já possui um empréstimo ativo para este livro.'},
                            status=status.HTTP_400_BAD_REQUEST)
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
                      description=f'Solicitou empréstimo via API: {book.title}', request=request)
        return Response(ReservationSerializer(reservation).data, status=status.HTTP_201_CREATED)


class ConfirmLoanAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk, status='PENDING')
        reservation.confirm_loan()
        ActionLog.log(user=request.user, action='BOOK_RESERVE',
                      description=f'Empréstimo confirmado via API: {reservation.book.title}',
                      request=request)
        return Response({
            'message': 'Empréstimo confirmado.',
            'loan': ReservationSerializer(reservation).data,
        })


class ReturnBookAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)
        if reservation.status not in ('ACTIVE', 'OVERDUE', 'PENDING'):
            return Response({'error': 'Este empréstimo não pode ser devolvido.'},
                            status=status.HTTP_400_BAD_REQUEST)
        fine = reservation.process_return()
        ActionLog.log(user=request.user, action='RESERVATION_CANCEL',
                      description=f'Devolução via API: {reservation.book.title} (multa: R$ {fine:.2f})',
                      request=request)
        return Response({
            'message': 'Devolução registrada com sucesso.',
            'fine_amount': str(fine),
            'overdue_days': reservation.overdue_days,
            'total_amount': str(reservation.total_amount),
            'loan': ReservationSerializer(reservation).data,
        })


class MarkFinePaidAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk, status='RETURNED')
        if reservation.fine_amount <= 0:
            return Response({'error': 'Este empréstimo não possui multa.'}, status=status.HTTP_400_BAD_REQUEST)
        reservation.fine_paid = True
        reservation.save()
        ActionLog.log(user=request.user, action='OTHER',
                      description=f'Multa paga registrada via API: R$ {reservation.fine_amount:.2f}',
                      request=request)
        return Response({'message': f'Multa de R$ {reservation.fine_amount:.2f} marcada como paga.'})


class CancelReservationAPIView(APIView):
    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
        if reservation.status not in ['PENDING']:
            return Response({'error': 'Apenas solicitações pendentes podem ser canceladas.'},
                            status=status.HTTP_400_BAD_REQUEST)
        reservation.status = 'CANCELLED'
        reservation.save()
        reservation.book.available_copies += 1
        reservation.book.save()
        ActionLog.log(user=request.user, action='RESERVATION_CANCEL',
                      description=f'Cancelou solicitação via API: {reservation.book.title}',
                      request=request)
        return Response({'message': 'Solicitação cancelada.'})


class CommentAPIView(APIView):
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        serializer = CommentSerializer(data={**request.data, 'book': book.pk})
        if serializer.is_valid():
            comment = serializer.save(user=request.user, book=book)
            ActionLog.log(user=request.user, action='COMMENT_ADD',
                          description=f'Comentou via API: {book.title}', request=request)
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RateBookAPIView(APIView):
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        score = request.data.get('score')
        try:
            score = int(score)
            if not (1 <= score <= 5):
                raise ValueError
        except (ValueError, TypeError):
            return Response({'error': 'Nota deve ser entre 1 e 5.'}, status=status.HTTP_400_BAD_REQUEST)
        rating, _ = Rating.objects.update_or_create(
            user=request.user, book=book, defaults={'score': score}
        )
        ActionLog.log(user=request.user, action='RATING_ADD',
                      description=f'Avaliou via API: {book.title} com {score}/5', request=request)
        return Response(RatingSerializer(rating).data, status=status.HTTP_201_CREATED)


class ReservationListAPIView(generics.ListAPIView):
    serializer_class = ReservationSerializer

    def get_queryset(self):
        qs = Reservation.objects.select_related('user', 'book').order_by('-reserved_at')
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)

        status_filter = self.request.query_params.get('status')
        overdue_only = self.request.query_params.get('overdue')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if overdue_only == '1':
            from datetime import date
            qs = qs.filter(status__in=['ACTIVE', 'OVERDUE'], due_date__lt=date.today())
        return qs


class LoanFinancialSummaryAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from django.db.models import Sum, Count, Q
        loans = Reservation.objects.all()

        total_revenue = loans.filter(status='RETURNED').aggregate(
            total=Sum('rental_price_snapshot'))['total'] or Decimal('0.00')
        total_fines_charged = loans.filter(status='RETURNED').aggregate(
            total=Sum('fine_amount'))['total'] or Decimal('0.00')
        total_fines_paid = loans.filter(status='RETURNED', fine_paid=True).aggregate(
            total=Sum('fine_amount'))['total'] or Decimal('0.00')
        total_fines_pending = total_fines_charged - total_fines_paid

        from datetime import date
        overdue_loans = loans.filter(
            status__in=['ACTIVE', 'OVERDUE'], due_date__lt=date.today()
        )

        return Response({
            'receita_emprestimos': str(total_revenue),
            'total_multas_cobradas': str(total_fines_charged),
            'total_multas_pagas': str(total_fines_paid),
            'total_multas_pendentes': str(total_fines_pending),
            'emprestimos_em_atraso': overdue_loans.count(),
            'emprestimos_ativos': loans.filter(status='ACTIVE').count(),
            'emprestimos_pendentes': loans.filter(status='PENDING').count(),
            'total_emprestimos': loans.count(),
            'total_devolvidos': loans.filter(status='RETURNED').count(),
        })


class CategoryListAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
