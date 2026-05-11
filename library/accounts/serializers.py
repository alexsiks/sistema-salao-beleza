from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import UserProfile, ActionLog


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['phone', 'cep', 'logradouro', 'numero', 'complemento',
                  'bairro', 'cidade', 'estado', 'bio', 'full_address', 'updated_at']
        read_only_fields = ['full_address', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'is_staff', 'date_joined', 'last_login', 'profile', 'token']
        read_only_fields = ['id', 'is_staff', 'date_joined', 'last_login', 'token']

    def get_token(self, obj):
        if self.context.get('include_token'):
            token, _ = Token.objects.get_or_create(user=obj)
            return token.key
        return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'token']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'As senhas não coincidem.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def get_token(self, obj):
        token, _ = Token.objects.get_or_create(user=obj)
        return token.key


class ActionLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = ActionLog
        fields = ['id', 'user', 'user_username', 'action', 'action_display',
                  'description', 'ip_address', 'path', 'method', 'timestamp', 'extra_data']
        read_only_fields = fields
