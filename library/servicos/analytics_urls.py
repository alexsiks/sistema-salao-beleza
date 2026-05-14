from django.urls import path
from . import analytics_views

urlpatterns = [
    path('analytics/summary/',       analytics_views.AnalyticsSummaryView.as_view(),       name='api_analytics_summary'),
    path('analytics/services/',      analytics_views.AnalyticsServicesView.as_view(),       name='api_analytics_services'),
    path('analytics/categories/',    analytics_views.AnalyticsCategoriesView.as_view(),     name='api_analytics_categories'),
    path('analytics/appointments/',  analytics_views.AnalyticsAppointmentsView.as_view(),   name='api_analytics_appointments'),
    path('analytics/professionals/', analytics_views.AnalyticsProfessionalsView.as_view(),  name='api_analytics_professionals'),
    path('analytics/users/',         analytics_views.AnalyticsUsersView.as_view(),          name='api_analytics_users'),
    path('analytics/logs/',          analytics_views.AnalyticsLogsView.as_view(),           name='api_analytics_logs'),
]
