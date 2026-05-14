from django.urls import path
from . import api_views

urlpatterns = [
    path('config/', api_views.SalonConfigAPIView.as_view(), name='api_salon_config'),

    path('categories/', api_views.ServiceCategoryListAPIView.as_view(), name='api_categories'),

    path('services/', api_views.ServiceListAPIView.as_view(), name='api_services'),
    path('services/<int:pk>/', api_views.ServiceDetailAPIView.as_view(), name='api_service_detail'),

    path('professionals/', api_views.ProfessionalListAPIView.as_view(), name='api_professionals'),

    path('available-slots/', api_views.AvailableSlotsAPIView.as_view(), name='api_available_slots'),

    path('appointments/', api_views.AppointmentListAPIView.as_view(), name='api_appointments'),
    path('appointments/<int:pk>/', api_views.AppointmentDetailAPIView.as_view(), name='api_appointment_detail'),
    path('appointments/book/', api_views.BookAppointmentAPIView.as_view(), name='api_book'),
    path('appointments/<int:pk>/confirm/', api_views.ConfirmAppointmentAPIView.as_view(), name='api_confirm'),
    path('appointments/<int:pk>/cancel/', api_views.CancelAppointmentAPIView.as_view(), name='api_cancel'),
    path('appointments/<int:pk>/complete/', api_views.CompleteAppointmentAPIView.as_view(), name='api_complete'),

    path('financial/', api_views.FinancialSummaryAPIView.as_view(), name='api_financial'),
]
