from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from accounts.managers import CustomUserManager
from accounts.validators import PhoneNumberValidator, LettersDigitsSpacesUnderscoreValidator


# Create your models here.

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="Имейл адрес")
    username =models.CharField(
        unique=True,
        max_length=30,
        verbose_name="Потребителско име",
        validators=[LettersDigitsSpacesUnderscoreValidator()]
    )

    first_name = models.CharField(max_length=50, verbose_name="Име")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")

    phone_number = models.CharField(
        validators=[PhoneNumberValidator(),],
        max_length=17,
        blank=True,
        null=True,
        verbose_name="Телефон за връзка"
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_staff = models.BooleanField(
        default=False,
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', ]

    def __str__(self):
        return self.email
    class Meta:
        verbose_name = 'Потребител'
        verbose_name_plural = 'Потребители'
