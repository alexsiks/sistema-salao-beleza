from django.urls import path
from . import analytics_views

urlpatterns = [
    path('analytics/summary/',     analytics_views.AnalyticsSummaryView.as_view(),      name='api_analytics_summary'),
    path('analytics/books/',       analytics_views.AnalyticsBooksView.as_view(),         name='api_analytics_books'),
    path('analytics/reservations/',analytics_views.AnalyticsReservationsView.as_view(),  name='api_analytics_reservations'),
    path('analytics/ratings/',     analytics_views.AnalyticsRatingsView.as_view(),       name='api_analytics_ratings'),
    path('analytics/users/',       analytics_views.AnalyticsUsersView.as_view(),         name='api_analytics_users'),
    path('analytics/logs/',        analytics_views.AnalyticsLogsView.as_view(),          name='api_analytics_logs'),
    path('analytics/categories/',  analytics_views.AnalyticsCategoriesView.as_view(),    name='api_analytics_categories'),
]
