from django.contrib import admin
from .models import Book, Category, Reservation, Comment, Rating, LibraryConfig


@admin.register(LibraryConfig)
class LibraryConfigAdmin(admin.ModelAdmin):
    list_display = ('fine_per_day', 'max_loan_days')

    def has_add_permission(self, request):
        return not LibraryConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'publisher', 'year', 'total_copies',
                    'available_copies', 'rental_price', 'average_rating', 'created_at')
    list_filter = ('categories', 'year', 'created_at')
    search_fields = ('title', 'author', 'isbn', 'publisher')
    filter_horizontal = ('categories',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'average_rating', 'rating_count')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status', 'reserved_at', 'loan_date',
                    'due_date', 'returned_at', 'rental_price_snapshot',
                    'fine_amount', 'fine_paid')
    list_filter = ('status', 'fine_paid', 'reserved_at')
    search_fields = ('user__username', 'book__title')
    readonly_fields = ('reserved_at', 'rental_price_snapshot', 'fine_per_day_snapshot',
                       'overdue_days', 'calculated_fine', 'total_amount')

    def overdue_days(self, obj):
        return obj.overdue_days
    overdue_days.short_description = 'Dias em Atraso'

    def calculated_fine(self, obj):
        return f'R$ {obj.calculated_fine:.2f}'
    calculated_fine.short_description = 'Multa Calculada'

    def total_amount(self, obj):
        return f'R$ {obj.total_amount:.2f}'
    total_amount.short_description = 'Total'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'content', 'is_visible', 'created_at')
    list_filter = ('is_visible', 'created_at')
    search_fields = ('user__username', 'book__title', 'content')


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'score', 'created_at')
    list_filter = ('score', 'created_at')
    search_fields = ('user__username', 'book__title')
