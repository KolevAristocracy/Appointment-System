import datetime

# from django.shortcuts import render
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from appointment.models import Service, Professional, Appointment
from appointment.serializers import ServiceSerializer, ProfessionalSerializer, AppointmentSerializer


# 1 API, which returns a list with the services (GET)
class ServiceListView(generics.ListAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


# 2 API, which returns a list with the employees / professionals (GET)
class ProfessionalListView(generics.ListAPIView):
    queryset = Professional.objects.filter(is_active=True)
    serializer_class = ProfessionalSerializer


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

            if not date_str or not pro_id:
                return Response({"грешка": "Липсва дата или служител"}, status=400)

            # Parse date
            try:
                target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"грешка": "Невалиден формат на дата"}, status=400)

            # 1. Define Working Hours (Hardcoded for now, ideally from DB)
            start_hour = 10
            end_hour = 18  # The last slot will be 17:30 if closes at 18:00

            # 2. Generate all posсible 30-min slots for that day
            all_slots = []
            current_time = datetime.time(start_hour, 0)
            end_time = datetime.time(end_hour, 0)

            while current_time < end_time:
                all_slots.append(current_time)
                # Add 30 minutes
                dt = datetime.datetime.combine(datetime.date.today(), current_time) + datetime.timedelta(minutes=30)
                current_time = dt.time()

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
                dummy_date = datetime.date(2000, 1, 1)  # random date just for checking
                full_start = datetime.datetime.combine(dummy_date, start_time)
                full_end = full_start + booking.service.duration

                busy_intervals.append((full_start.time(), full_end.time()))

            # 4. Filter logic
            available_slots = []
            now = datetime.datetime.now()

            for slot in all_slots:
                is_busy = False

                # Check for Double Booking
                for start, end in busy_intervals:
                    # Logic: If slot is >= start and slot is < end
                    # Example: Slot 10:30. Interval 10:00-11:00.
                    # 10:00 <= 10:30 < 11:00 -> TRUE (IT'S BUSY!)
                    if start <= slot < end:
                        is_busy = True
                        break # No point of checking the other intervals
                if is_busy:
                    continue # skip this slot

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
        serializer.save(user=user)
