from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import SET_NULL
from django.utils import timezone
import datetime

from accounts.validators import PhoneNumberValidator
from appointmentSystem import settings

class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name="Име на услугата")
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена (лв. / €)")
    duration = models.DurationField(verbose_name="Продължителност") # Example 00:30:00

    def __str__(self):
        return f"{self.name} {self.duration}"

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

class Professional(models.Model):
    name = models.CharField(max_length=100, verbose_name="Име на служителя")
    is_active = models.BooleanField(default=True, verbose_name="Активен служител")
    # Here I also can add open hours for the future

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Служител"
        verbose_name_plural = "Служители"



class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', '⏳ Изчаква'),
        ('confirmed', '✅ Потвърден'),
        ('cancelled', '❌ Отказан'),
        ('completed', '🏁 Приключен'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )

    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="Служител"
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        verbose_name="Услуга"
    )

    # Info for a client (always filled, even if no profile presented)
    client_name = models.CharField(max_length=100, verbose_name="Име на клиента")
    client_phone = models.CharField(
        validators=[PhoneNumberValidator(),],
        max_length=17,
        verbose_name="Телефон за връзка",
    )

    client_email = models.EmailField(blank=True, null=True, verbose_name="Имейл за контакт")

    # --- Time and Status ---
    date = models.DateField(verbose_name="Дата")
    time = models.TimeField(verbose_name="Час")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']
        verbose_name = 'Резервация'
        verbose_name_plural = 'Резервации'

    def __str__(self):
        return f"{self.client_name} - {self.date} {self.time}"

    # --- Business Logic ---
    def end_time(self):
        # calculate the end time based of the services
        # Sum date and time, we add duration and return only the time
        booking_datetime = datetime.datetime.combine(self.date, self.time)
        if timezone.is_naive(booking_datetime):
            booking_datetime = timezone.make_aware(booking_datetime)

        if booking_datetime < timezone.now():
            raise ValidationError("Не можете да запазвате час в миналото!")

    @property
    def is_guest(self):
        return self.user is None

    def get_display_name(self):
        if self.user:
            return f"{self.client_name} (Регистриран)"
        else:
            return f"{self.client_name} (Гост)"


