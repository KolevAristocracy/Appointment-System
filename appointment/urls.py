from django.urls import path
from django.views.generic import TemplateView

from appointment.views import ServiceListView, ProfessionalListView, CreateAppointmentView, AvailableSlotsView, \
    ProfessionalScheduleView

urlpatterns = [
    path('client/', TemplateView.as_view(template_name='index.html'), name='client-home'),
    path('services/', ServiceListView.as_view(), name='service-list'),
    path('professionals/', ProfessionalListView.as_view(), name='professional-list'),
    path('book/', CreateAppointmentView.as_view(), name='book-appointment'),
    path('slots/', AvailableSlotsView.as_view(), name='available-slots'),
    path('my-schedule/', ProfessionalScheduleView.as_view(), name='my-schedule')

]