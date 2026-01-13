import datetime

from django.utils import timezone
from rest_framework import serializers

from appointment.models import Service, Professional, Appointment, BusinessCategory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessCategory
        fields = ['slug', 'name', 'icon']
# Serializer for Dashboard (Read-Only)
class AppointmentListSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'date', 'time', 'client_name', 'client_phone', 'service_name', 'status', 'status_display']


# Show the services to the Front-end
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'price', 'description', 'duration']


# Show the Professional (employees)
class ProfessionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professional
        fields = ['id', 'name']


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        # These fields are expected from the JavaScript (client)
        fields = [
            'id',
            'service',
            'professional',
            'date',
            'time',
            'client_name',
            'client_phone',
            'client_email',
        ]

    def validate(self, data):
        """
        Professional validation logic to prevent logic errors and security issues.
        """

        # ALLOWED_MINUTES = [0, 30]

        # Take the required params from the request
        booking_date = data['date']
        booking_time = data['time']
        service = data['service']
        professional = data['professional']

        # Calculate when the appointment starts and ends
        # Using fake date just for checking
        dummy_date = datetime.date(2000, 1, 1)
        new_start = datetime.datetime.combine(dummy_date, booking_time)
        new_end = new_start + service.duration

        # Take all booking for this date and professional
        existing_appointments = Appointment.objects.filter(
            professional=professional,
            date=booking_date
        ).exclude(status='cancelled').select_related('service')

        # Overlap Logic
        for appt in existing_appointments:
            # Calculate start and end of existing appointment
            existing_start = datetime.datetime.combine(dummy_date, appt.time)
            existing_end = existing_start + appt.service.duration

            # Formula for overlap of 2 intervals
            # (StartA < EndB) and (EndA > StartB)
            # This catches all possibilities for overlap
            if new_start < existing_end and new_end > existing_start:
                raise serializers.ValidationError(
                    f"Този час се застъпва с друга резервация"
                    f" ({existing_start.strftime('%H:%M')} - {existing_end.strftime('%H:%M')})."
                )
        return data