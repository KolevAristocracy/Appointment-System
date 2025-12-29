from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

UserModel = get_user_model()

# Register your models here.
@admin.register(UserModel)
class UserModelAdmin(UserAdmin):
    list_display = ["username", "email"]
    readonly_fields = ["password"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (("Personal info"), {"fields": ("email",)}),
        (
            ("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (("Important Dates"), {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )