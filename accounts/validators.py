import re

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class PhoneNumberValidator:
    def __init__(self, message: str=None) -> None:
        self.message = message
        self.regex = re.compile(r'^\+?1?\d{9,15}$')

    @property
    def message(self) -> str:
        return self.__message

    @message.setter
    def message(self, value: str):
        self.__message = value or "Телефонният номер трябва да е във формат: '+359888123456' или '0888123456'."

    def __call__(self, value: str) -> None:
        if not self.regex.match(value):
            raise ValidationError(self.message)

    def __eq__(self, other):
        return isinstance(other, PhoneNumberValidator)


@deconstructible
class LettersDigitsSpacesUnderscoreValidator:
    def __init__(self, message: str=None) -> None:
        self.message = message

    @property
    def message(self) -> str:
        return self.__message

    @message.setter
    def message(self, value: str):
        self.__message = value or "*Allowed names contain letters, digits, spaces, and underscores."

    def __call__(self, value: str) -> None:
        for char in value:
            if not (char.isalnum() or char in [' ', '_']):
                raise ValidationError(self.message)