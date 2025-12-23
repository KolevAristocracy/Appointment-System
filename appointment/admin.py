from django.contrib import admin

from appointment.models import Appointment, Service, Professional


# Register your models here.

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'professional', 'client_name', 'service', 'date', 'status', ]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'price', 'duration']


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ['name']

