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
    path('my-loans/', views.my_reservations, name='my_reservations'),
    path('loan/<int:pk>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    path('loan/<int:pk>/confirm/', views.confirm_loan, name='confirm_loan'),
    path('loan/<int:pk>/return/', views.return_book, name='return_book'),
    path('loan/<int:pk>/fine-paid/', views.mark_fine_paid, name='mark_fine_paid'),
    path('loans/', views.all_reservations, name='all_reservations'),
    path('config/', views.library_config, name='library_config'),
]
