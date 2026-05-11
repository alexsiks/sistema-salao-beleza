from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import generics, status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ActionLog, UserProfile
from .serializers import UserSerializer, RegisterSerializer, ActionLogSerializer, UserProfileSerializer


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            ActionLog.log(user=user, action='REGISTER',
                          description=f'Registro via API: {user.username}', request=request,
                          extra_data={'username': user.username, 'email': user.email})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            ActionLog.log(user=user, action='LOGIN',
                          description=f'Login via API: {user.username}', request=request)
            serializer = UserSerializer(user, context={'include_token': True})
            return Response({'token': token.key, 'user': serializer.data})
        return Response({'error': 'Credenciais inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutAPIView(APIView):
    def post(self, request):
        ActionLog.log(user=request.user, action='LOGOUT',
                      description=f'Logout via API: {request.user.username}', request=request)
        request.user.auth_token.delete()
        return Response({'message': 'Logout realizado com sucesso.'})


class GetTokenAPIView(APIView):
    def get(self, request):
        token, _ = Token.objects.get_or_create(user=request.user)
        return Response({'token': token.key, 'username': request.user.username})


class MeAPIView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user, context={'include_token': True})
        return Response(serializer.data)


class ProfileUpdateAPIView(APIView):
    def put(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            user = request.user
            user.first_name = request.data.get('first_name', user.first_name)
            user.last_name = request.data.get('last_name', user.last_name)
            user.email = request.data.get('email', user.email)
            user.save()
            ActionLog.log(user=user, action='PROFILE_UPDATE',
                          description=f'Perfil atualizado via API: {user.username}', request=request)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListAPIView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return User.objects.select_related('profile').order_by('-date_joined')


class UserDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.select_related('profile').all()

    def perform_destroy(self, instance):
        ActionLog.log(user=self.request.user, action='USER_DELETE',
                      description=f'Usuário excluído: {instance.username}', request=self.request)
        instance.delete()


class ActionLogAPIView(generics.ListAPIView):
    serializer_class = ActionLogSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = ActionLog.objects.select_related('user').order_by('-timestamp')
        user_id = self.request.query_params.get('user')
        action = self.request.query_params.get('action')
        if user_id:
            qs = qs.filter(user_id=user_id)
        if action:
            qs = qs.filter(action=action)
        return qs
