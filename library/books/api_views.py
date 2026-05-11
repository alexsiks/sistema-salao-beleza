from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Book, Category, Reservation, Comment, Rating
from .serializers import (BookListSerializer, BookDetailSerializer,
                           ReservationSerializer, CommentSerializer,
                           RatingSerializer, CategorySerializer)
from accounts.models import ActionLog


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
            user=request.user, book=book, status__in=['PENDING', 'ACTIVE']
        ).exists()
        if existing:
            return Response({'error': 'Você já possui uma reserva ativa.'}, status=status.HTTP_400_BAD_REQUEST)
        reservation = Reservation.objects.create(user=request.user, book=book, status='PENDING')
        book.available_copies -= 1
        book.save()
        ActionLog.log(user=request.user, action='BOOK_RESERVE',
                      description=f'Reservou via API: {book.title}', request=request)
        return Response(ReservationSerializer(reservation).data, status=status.HTTP_201_CREATED)


class CancelReservationAPIView(APIView):
    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
        if reservation.status not in ['PENDING', 'ACTIVE']:
            return Response({'error': 'Reserva não pode ser cancelada.'}, status=status.HTTP_400_BAD_REQUEST)
        reservation.status = 'CANCELLED'
        reservation.save()
        reservation.book.available_copies += 1
        reservation.book.save()
        ActionLog.log(user=request.user, action='RESERVATION_CANCEL',
                      description=f'Cancelou reserva via API: {reservation.book.title}', request=request)
        return Response({'message': 'Reserva cancelada.'})


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
        if self.request.user.is_staff:
            return Reservation.objects.select_related('user', 'book').order_by('-reserved_at')
        return Reservation.objects.filter(user=self.request.user).select_related('book').order_by('-reserved_at')


class CategoryListAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
