from django.urls import path
from . import views

app_name = 'servicos'

urlpatterns = [
    path('', views.service_list, name='list'),
    path('<int:pk>/', views.service_detail, name='detail'),
    path('<int:pk>/agendar/', views.book_appointment, name='book'),
    path('meus-agendamentos/', views.my_appointments, name='my_appointments'),
    path('agendamento/<int:pk>/cancelar/', views.cancel_appointment, name='cancel_appointment'),

    # Admin
    path('servico/cadastrar/', views.service_create, name='service_create'),
    path('servico/<int:pk>/editar/', views.service_edit, name='service_edit'),
    path('servico/<int:pk>/excluir/', views.service_delete, name='service_delete'),
    path('agendamentos/', views.all_appointments, name='all_appointments'),
    path('agendamento/<int:pk>/confirmar/', views.confirm_appointment, name='confirm_appointment'),
    path('agendamento/<int:pk>/cancelar-admin/', views.reject_appointment, name='reject_appointment'),
    path('agendamento/<int:pk>/concluir/', views.complete_appointment, name='complete_appointment'),
    path('agendamento/<int:pk>/nao-compareceu/', views.no_show_appointment, name='no_show'),
    path('profissionais/', views.professionals_list, name='professionals'),
    path('configuracoes/', views.salon_config, name='salon_config'),
    path('painel/', views.dashboard_24h, name='dashboard'),

    # AJAX
    path('horarios-disponiveis/', views.available_slots_api, name='available_slots'),
]
