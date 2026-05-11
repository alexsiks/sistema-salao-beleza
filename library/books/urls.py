from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.book_list, name='list'),
    path('<int:pk>/', views.book_detail, name='detail'),
    path('create/', views.book_create, name='create'),
    path('<int:pk>/edit/', views.book_edit, name='edit'),
    path('<int:pk>/delete/', views.book_delete, name='delete'),
    path('<int:pk>/reserve/', views.book_reserve, name='reserve'),
    path('<int:pk>/comment/', views.add_comment, name='comment'),
    path('<int:pk>/rate/', views.add_rating, name='rate'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('reservation/<int:pk>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    path('reservations/', views.all_reservations, name='all_reservations'),
]
