from django.contrib import admin
from .models import SalonConfig, ServiceCategory, Service, Professional, Appointment


@admin.register(SalonConfig)
class SalonConfigAdmin(admin.ModelAdmin):
    list_display = ('salon_name', 'phone', 'open_time', 'close_time', 'slot_minutes')

    def has_add_permission(self, request):
        return not SalonConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'description')
    search_fields = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'duration_minutes', 'price', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'is_active', 'upcoming_appointments')
    list_filter = ('is_active',)
    filter_horizontal = ('services',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'service', 'professional', 'date', 'start_time',
                    'end_time', 'status', 'price_snapshot')
    list_filter = ('status', 'date', 'professional')
    search_fields = ('client__username', 'client__first_name', 'service__name')
    readonly_fields = ('created_at', 'price_snapshot', 'duration_snapshot')
    date_hierarchy = 'date'
