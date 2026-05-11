from django.urls import path
from . import api_views

urlpatterns = [
    path('books/', api_views.BookListAPIView.as_view(), name='api_book_list'),
    path('books/<int:pk>/', api_views.BookDetailAPIView.as_view(), name='api_book_detail'),
    path('books/<int:pk>/reserve/', api_views.ReserveBookAPIView.as_view(), name='api_book_reserve'),
    path('books/<int:pk>/comment/', api_views.CommentAPIView.as_view(), name='api_book_comment'),
    path('books/<int:pk>/rate/', api_views.RateBookAPIView.as_view(), name='api_book_rate'),
    path('reservations/', api_views.ReservationListAPIView.as_view(), name='api_reservations'),
    path('reservations/<int:pk>/cancel/', api_views.CancelReservationAPIView.as_view(), name='api_cancel_reservation'),
    path('categories/', api_views.CategoryListAPIView.as_view(), name='api_categories'),
]
