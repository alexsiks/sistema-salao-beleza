from django.urls import path
from . import api_views

urlpatterns = [
    path('auth/register/', api_views.RegisterAPIView.as_view(), name='api_register'),
    path('auth/login/', api_views.LoginAPIView.as_view(), name='api_login'),
    path('auth/logout/', api_views.LogoutAPIView.as_view(), name='api_logout'),
    path('auth/token/', api_views.GetTokenAPIView.as_view(), name='api_token'),
    path('users/', api_views.UserListAPIView.as_view(), name='api_user_list'),
    path('users/<int:pk>/', api_views.UserDetailAPIView.as_view(), name='api_user_detail'),
    path('users/me/', api_views.MeAPIView.as_view(), name='api_me'),
    path('users/me/profile/', api_views.ProfileUpdateAPIView.as_view(), name='api_profile_update'),
    path('logs/', api_views.ActionLogAPIView.as_view(), name='api_logs'),
]
