from django.contrib import admin
from .models import Book, Category, Reservation, Comment, Rating


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'publisher', 'year', 'total_copies',
                    'available_copies', 'average_rating', 'created_at')
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
    list_display = ('user', 'book', 'status', 'reserved_at', 'pickup_deadline', 'returned_at')
    list_filter = ('status', 'reserved_at')
    search_fields = ('user__username', 'book__title')
    readonly_fields = ('reserved_at',)


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
