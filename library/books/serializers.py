from rest_framework import serializers
from .models import Book, Category, Reservation, Comment, Rating


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class RatingSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'user', 'user_username', 'book', 'score', 'created_at']
        read_only_fields = ['id', 'user', 'user_username', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'user_username', 'user_full_name', 'book',
                  'content', 'created_at', 'updated_at', 'is_visible']
        read_only_fields = ['id', 'user', 'user_username', 'user_full_name',
                            'created_at', 'updated_at', 'is_visible']

    def get_user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class BookListSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField(read_only=True)
    rating_count = serializers.IntegerField(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'publisher', 'year', 'cover_image',
                  'categories', 'available_copies', 'total_copies', 'is_available',
                  'average_rating', 'rating_count', 'created_at']


class BookDetailSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField(read_only=True)
    rating_count = serializers.IntegerField(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), many=True, write_only=True,
        source='categories', required=False
    )
    comments = CommentSerializer(many=True, read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'publisher', 'year', 'description',
                  'cover_image', 'categories', 'category_ids', 'total_copies',
                  'available_copies', 'is_available', 'average_rating', 'rating_count',
                  'comments', 'created_by_username', 'created_at', 'updated_at']
        read_only_fields = ['id', 'available_copies', 'is_available', 'average_rating',
                            'rating_count', 'created_by_username', 'created_at', 'updated_at']


class ReservationSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_author = serializers.CharField(source='book.author', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Reservation
        fields = ['id', 'user', 'user_username', 'book', 'book_title', 'book_author',
                  'status', 'status_display', 'reserved_at', 'pickup_deadline',
                  'returned_at', 'notes']
        read_only_fields = ['id', 'user', 'user_username', 'book_title', 'book_author',
                            'status', 'status_display', 'reserved_at']
