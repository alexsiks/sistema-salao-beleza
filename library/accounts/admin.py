from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, ActionLog


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'
    fields = ('phone', 'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'bio')


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'path', 'method', 'ip_address', 'timestamp')
    list_filter = ('action', 'method', 'timestamp')
    search_fields = ('user__username', 'user__email', 'description', 'path', 'ip_address')
    readonly_fields = ('user', 'action', 'description', 'ip_address', 'user_agent',
                       'path', 'method', 'timestamp', 'extra_data')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
