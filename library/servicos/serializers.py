from rest_framework import serializers
from .models import Service, ServiceCategory, Professional, Appointment, SalonConfig


class SalonConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalonConfig
        fields = ['salon_name', 'phone', 'address', 'open_time', 'close_time',
                  'slot_minutes', 'max_advance_days', 'cancellation_hours']


class ServiceCategorySerializer(serializers.ModelSerializer):
    service_count = serializers.SerializerMethodField()

    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'icon', 'description', 'service_count']

    def get_service_count(self, obj):
        return obj.services.filter(is_active=True).count()


class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    duration_display = serializers.CharField(read_only=True)
    professionals_count = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'duration_minutes', 'duration_display',
                  'price', 'category', 'category_name', 'image', 'is_active',
                  'professionals_count', 'created_at']
        read_only_fields = ['id', 'duration_display', 'professionals_count', 'created_at']

    def get_professionals_count(self, obj):
        return obj.professionals.filter(is_active=True).count()


class ProfessionalSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    services = ServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Professional
        fields = ['id', 'full_name', 'username', 'bio', 'photo',
                  'services', 'is_active', 'upcoming_appointments']
        read_only_fields = ['id', 'full_name', 'username', 'upcoming_appointments']


class AppointmentSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    client_username = serializers.CharField(source='client.username', read_only=True)
    professional_name = serializers.SerializerMethodField()
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_duration = serializers.IntegerField(source='service.duration_minutes', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id', 'client', 'client_name', 'client_username',
            'professional', 'professional_name',
            'service', 'service_name', 'service_duration',
            'date', 'start_time', 'end_time',
            'status', 'status_display',
            'notes', 'internal_notes',
            'price_snapshot', 'duration_snapshot',
            'cancel_reason',
            'is_upcoming', 'can_cancel',
            'created_at',
        ]
        read_only_fields = [
            'id', 'client', 'client_name', 'client_username',
            'professional_name', 'service_name', 'service_duration',
            'status', 'status_display', 'end_time',
            'price_snapshot', 'duration_snapshot',
            'is_upcoming', 'can_cancel', 'created_at',
        ]

    def get_client_name(self, obj):
        return obj.client.get_full_name() or obj.client.username

    def get_professional_name(self, obj):
        if obj.professional:
            return obj.professional.full_name
        return 'Sem profissional definido'

    def get_can_cancel(self, obj):
        return obj.can_cancel()
