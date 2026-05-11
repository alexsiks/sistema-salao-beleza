from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',       views.login_view,         name='login'),
    path('logout/',      views.logout_view,         name='logout'),
    path('register/',    views.register_view,       name='register'),
    path('profile/',     views.profile_view,        name='profile'),
    path('token/',       views.token_view,          name='token'),
    path('cep/',         views.lookup_cep,          name='cep_lookup'),
    path('cep/public/',  views.lookup_cep_public,   name='cep_lookup_public'),
    path('users/',       views.user_list_view,      name='user_list'),
    path('logs/',        views.action_log_view,     name='action_logs'),
]
