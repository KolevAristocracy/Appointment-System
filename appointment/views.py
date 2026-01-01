import datetime
import textwrap
from unicodedata import category

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
# from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from appointment.models import Service, Professional, Appointment
from appointment.serializers import ServiceSerializer, ProfessionalSerializer, AppointmentSerializer, \
    AppointmentListSerializer


# 1 API, which returns a list with the services (GET)
class ServiceListView(generics.ListAPIView):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        queryset = Service.objects.all()

        # Filter by category # (if the user chose massage)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by professional (if the user chose first a professional)
        pro_id = self.request.query_params.get('professional')
        if pro_id:
            queryset = queryset.filter(professionals__id=pro_id)

        return queryset

# 2 API, which returns a list with the employees / professionals (GET)
class ProfessionalListView(generics.ListAPIView):
    serializer_class = ProfessionalSerializer

    def get_queryset(self):
        # get all active professionals
        queryset = Professional.objects.filter(is_active=True)
        service_id = self.request.query_params.get('service')

        if service_id:
            # "Give me professionals which are skilled in service including this ID"
            queryset = queryset.filter(services__pk=service_id).distinct()  # check later if pk raises issues (change to id if)

        return queryset

# 3 API, which returns available 30-minutes slots (GET)
class AvailableSlotsView(APIView):
    """
    Returns a list of available 30-minute slots for a specific professional and date.
    Query Params: ?date=YYYY-MM-DD&professional=1
    """

    def get(self, request):
        try:
            date_str = request.query_params.get('date')
            pro_id = request.query_params.get('professional')
            service_id = request.query_params.get('service')

            if not date_str or not pro_id or not service_id:
                return Response({"грешка": "Липсва дата, услуга или служител"}, status=400)

            # Get the duration of the service for the new appointment and the professional work time
            try:
                service_obj = Service.objects.get(pk=service_id)
                professional_obj = Professional.objects.get(pk=pro_id)
            except Service.DoesNotExist:
                return Response({"грешка": "Невалидна услуга"}, status=400)

            new_duration = service_obj.duration

            # Parse date
            try:
                target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"грешка": "Невалиден формат на дата"}, status=400)

            # 1. Define Working Hours of professional
            current_time = professional_obj.start_work_time
            end_work_time = professional_obj.end_work_time

            # 2. Generate all possible 30-min slots for that day
            all_slots = []

            dummy_date = datetime.date(2000, 1, 1)
            while True:
                # Validation if duration is after working hours
                slot_start_dt = datetime.datetime.combine(dummy_date, current_time)
                slot_end_dt = slot_start_dt + new_duration

                limit_dt = datetime.datetime.combine(dummy_date, end_work_time)

                if slot_end_dt > limit_dt:
                    break # Stop generating of new  slots, because we go outside the working hours

                all_slots.append(current_time)

                # Adding 30 minutes for the next slot
                next_slot_dt = slot_start_dt + datetime.timedelta(minutes=30)
                current_time = next_slot_dt.time()

            # 3. Fetch existing booking
            # Взимаме резервациите, НО заедно с информация за услугата!
            # select_related('service') прави заявката бърза (JOIN в SQL)
            booked_slots = Appointment.objects.filter(
                professional_id=pro_id,
                date=target_date
            ).exclude(status='cancelled').select_related('service')

            # Creating list with busy intervals
            # [(10:00, 11:00), (14:00, 14:30)]
            busy_intervals = []

            for booking in booked_slots:
                # start time of the appointment
                start_time = booking.time

                # End = Start + Duration of the service
                full_start = datetime.datetime.combine(dummy_date, start_time)  # check the logic later
                full_end = full_start + booking.service.duration
                busy_intervals.append((full_start.time(), full_end.time()))

            # 4. Filter logic
            available_slots = []
            now = datetime.datetime.now()

            for slot in all_slots:
                # Calculate the intervals of the potential new appointment
                proposed_start = datetime.datetime.combine(dummy_date, slot)
                proposed_end = proposed_start + new_duration

                is_busy = False

                # Check for Double Booking
                for start, end in busy_intervals:
                    # Logic: (StartA < EndB) and (EndA > StartB)
                    # convert in time because can't compare datetime with time
                    if proposed_start.time() < end and proposed_end.time() > start:
                        is_busy = True
                        break  # No point of checking the other intervals

                if is_busy:
                    continue  # skip this slot

                # Check for pastime (if it's today)
                slot_full_datetime = datetime.datetime.combine(target_date, slot)
                if slot_full_datetime < now:
                    continue

                available_slots.append(slot.strftime("%H:%M"))

            return Response(available_slots)

        except Exception as e:
            import traceback
            print(f"ГРЕШКА: {str(e)}")
            print(traceback.format_exc())  # Maybe have to be removed on deployment

            return Response({"error": str(e)}, status=500)


# 4 API, which create appointment (POST)
class CreateAppointmentView(generics.CreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    # If you want to save the logged-in user automatically:
    def perform_create(self, serializer):
        # If a user is logged in (not AnonymousUser), save it.
        user = self.request.user if self.request.user.is_authenticated else None
        appointment = serializer.save(user=user)

        # 2. Подготвяме имейл до КЛИЕНТА
        subject = f"Потвърждение за час: {appointment.date}"

        # 2. Използваме textwrap.dedent, за да махнем отстъпите
        # f-string-ът запазва променливите, но dedent маха празните места отляво
        message = textwrap.dedent(f"""
                    Здравейте, {appointment.client_name}!

                    Успешно запазихте час за:
                    --------------------------------
                    Услуга: {appointment.service.name}
                    При: {appointment.professional.name}
                    Дата: {appointment.date}
                    Час: {appointment.time}
                    --------------------------------

                    Ако искате да отмените, моля обадете се на 0888 123 456.

                    Поздрави,
                    Екипът на Салона
                """).strip()

        # Изпращаме (на теория)
        # В Console режим ще го видиш долу в терминала
        if appointment.client_email:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,  # От кого
                [appointment.client_email],  # До кого
                fail_silently=False,
            )

        # 3. (По желание) Имейл до СОБСТВЕНИКА
        # send_mail("Нова резервация!", f"Клиент {appointment.client_name} се записа...", ...)

class ProfessionalScheduleView(generics.ListAPIView):
    serializer_class = AppointmentListSerializer
    permission_classes = [IsAuthenticated] # Only logged-in users

    def get_queryset(self):
        user = self.request.user

        if not hasattr(user, 'professional_profile'):
            return Appointment.objects.none() # If It's just admin with no profile or client

        professional = user.professional_profile
        queryset = Appointment.objects.filter(professional=professional)

        # Get the date from the URL (or today's date by default)
        date_str = self.request.query_params.get('date')
        if date_str:
            queryset = queryset.filter(date=date_str)
        else:
            queryset = queryset.filter(date__gte=timezone.localdate())

        # return the appointments for the current professional and date
        return queryset.order_by('date', 'time')

class UpdateAppointmentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            appointment = Appointment.objects.get(
                pk=pk,
                professional__user=request.user
            )
        except Appointment.DoesNotExist:
            return Response({"error": "Резервацията не е намерена или нямате права."}, status=404)

        new_status = request.data.get('status')
        if new_status not in ['confirmed', 'cancelled', 'completed']:
            return Response({"error": "Невалиден статус"}, status=400)

        appointment.status = new_status
        appointment.save()

        return Response({"message": "Статусът е обновен успешно!"})


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    login_url = '/admin/login/'