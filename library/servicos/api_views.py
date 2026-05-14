from datetime import date, datetime, timedelta
from django.db.models import Q, Count, Sum
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Service, ServiceCategory, Professional, Appointment, SalonConfig
from .serializers import (ServiceSerializer, ServiceCategorySerializer,
                           ProfessionalSerializer, AppointmentSerializer,
                           SalonConfigSerializer)
from accounts.models import ActionLog


class SalonConfigAPIView(APIView):
    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get(self, request):
        return Response(SalonConfigSerializer(SalonConfig.get()).data)

    def put(self, request):
        s = SalonConfigSerializer(SalonConfig.get(), data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        s = SalonConfigSerializer(SalonConfig.get(), data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class ServiceCategoryListAPIView(generics.ListCreateAPIView):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class ServiceListAPIView(generics.ListCreateAPIView):
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = Service.objects.select_related('category').order_by('name')
        q = self.request.query_params.get('q')
        category = self.request.query_params.get('category')
        active_only = self.request.query_params.get('active', '1')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        if category:
            qs = qs.filter(category_id=category)
        if active_only == '1':
            qs = qs.filter(is_active=True)
        return qs


class ServiceDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class ProfessionalListAPIView(generics.ListAPIView):
    serializer_class = ProfessionalSerializer

    def get_queryset(self):
        qs = Professional.objects.filter(is_active=True).select_related('user')
        service_id = self.request.query_params.get('service')
        if service_id:
            qs = qs.filter(services__id=service_id)
        return qs


class AvailableSlotsAPIView(APIView):
    def get(self, request):
        service_id = request.query_params.get('service')
        professional_id = request.query_params.get('professional')
        date_str = request.query_params.get('date')

        if not service_id or not date_str:
            return Response({'error': 'Parâmetros obrigatórios: service, date'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Data inválida (use YYYY-MM-DD)'},
                            status=status.HTTP_400_BAD_REQUEST)

        if appt_date < date.today():
            return Response({'slots': [], 'date': date_str})

        service = get_object_or_404(Service, pk=service_id, is_active=True)
        config = SalonConfig.get()

        if professional_id:
            professional = get_object_or_404(Professional, pk=professional_id, is_active=True)
            slots = config.available_slots(appt_date, professional, service.duration_minutes)
        else:
            profs = service.professionals.filter(is_active=True)
            all_slots = set()
            for p in profs:
                s = config.available_slots(appt_date, p, service.duration_minutes)
                all_slots.update(s)
            slots = sorted(all_slots)

        return Response({
            'date': date_str,
            'service': service.name,
            'duration_minutes': service.duration_minutes,
            'slots': [s.strftime('%H:%M') for s in slots],
        })


class BookAppointmentAPIView(APIView):
    def post(self, request):
        service_id = request.data.get('service')
        professional_id = request.data.get('professional')
        date_str = request.data.get('date')
        start_time_str = request.data.get('start_time')
        notes = request.data.get('notes', '')

        if not service_id or not date_str or not start_time_str:
            return Response({'error': 'Campos obrigatórios: service, date, start_time'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
        except ValueError:
            return Response({'error': 'Formato inválido. Data: YYYY-MM-DD, Hora: HH:MM'},
                            status=status.HTTP_400_BAD_REQUEST)

        service = get_object_or_404(Service, pk=service_id, is_active=True)
        end_dt = datetime.combine(appt_date, start_time) + timedelta(minutes=service.duration_minutes)
        end_time = end_dt.time()

        professional = None
        if professional_id:
            professional = get_object_or_404(Professional, pk=professional_id, is_active=True)

        if professional:
            conflict = Appointment.objects.filter(
                professional=professional,
                date=appt_date,
                status__in=['PENDING', 'CONFIRMED'],
            ).filter(Q(start_time__lt=end_time, end_time__gt=start_time)).exists()
            if conflict:
                return Response({'error': 'Horário indisponível para este profissional.'},
                                status=status.HTTP_409_CONFLICT)

        appt = Appointment.objects.create(
            client=request.user,
            professional=professional,
            service=service,
            date=appt_date,
            start_time=start_time,
            end_time=end_time,
            notes=notes,
            price_snapshot=service.price,
            duration_snapshot=service.duration_minutes,
        )
        ActionLog.log(user=request.user, action='OTHER',
                      description=f'Agendamento via API: {service.name} em {appt_date}',
                      request=request)
        return Response(AppointmentSerializer(appt).data, status=status.HTTP_201_CREATED)


class AppointmentListAPIView(generics.ListAPIView):
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        qs = Appointment.objects.select_related(
            'client', 'professional__user', 'service'
        ).order_by('date', 'start_time')
        if not self.request.user.is_staff:
            qs = qs.filter(client=self.request.user)
        status_f = self.request.query_params.get('status')
        date_f = self.request.query_params.get('date')
        upcoming = self.request.query_params.get('upcoming')
        if status_f:
            qs = qs.filter(status=status_f)
        if date_f:
            qs = qs.filter(date=date_f)
        if upcoming == '1':
            qs = qs.filter(date__gte=date.today(), status__in=['PENDING', 'CONFIRMED'])
        return qs


class AppointmentDetailAPIView(generics.RetrieveAPIView):
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Appointment.objects.all()
        return Appointment.objects.filter(client=self.request.user)


class ConfirmAppointmentAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk, status='PENDING')
        appt.status = 'CONFIRMED'
        appt.save()
        ActionLog.log(user=request.user, action='OTHER',
                      description=f'Agendamento confirmado via API: {appt}',
                      request=request)
        return Response({'message': 'Agendamento confirmado.',
                         'appointment': AppointmentSerializer(appt).data})


class CancelAppointmentAPIView(APIView):
    def post(self, request, pk):
        if request.user.is_staff:
            appt = get_object_or_404(Appointment, pk=pk)
        else:
            appt = get_object_or_404(Appointment, pk=pk, client=request.user)
        config = SalonConfig.get()
        if not request.user.is_staff and not appt.can_cancel(config):
            return Response({'error': 'Cancelamento fora do prazo permitido.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if appt.status not in ('PENDING', 'CONFIRMED'):
            return Response({'error': 'Este agendamento não pode ser cancelado.'},
                            status=status.HTTP_400_BAD_REQUEST)
        appt.status = 'CANCELLED'
        appt.cancel_reason = request.data.get('reason', '')
        appt.save()
        return Response({'message': 'Agendamento cancelado.'})


class CompleteAppointmentAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk, status='CONFIRMED')
        appt.status = 'COMPLETED'
        appt.save()
        return Response({'message': 'Serviço concluído.',
                         'appointment': AppointmentSerializer(appt).data})


class FinancialSummaryAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        today = date.today()
        appts = Appointment.objects.all()
        receita = appts.filter(status='COMPLETED').aggregate(
            t=Sum('price_snapshot'))['t'] or 0
        return Response({
            'receita_total': str(receita),
            'agendamentos_hoje': appts.filter(date=today).count(),
            'agendamentos_pendentes': appts.filter(status='PENDING').count(),
            'agendamentos_confirmados': appts.filter(
                date__gte=today, status='CONFIRMED').count(),
            'agendamentos_concluidos': appts.filter(status='COMPLETED').count(),
            'agendamentos_cancelados': appts.filter(status='CANCELLED').count(),
            'total_agendamentos': appts.count(),
        })
