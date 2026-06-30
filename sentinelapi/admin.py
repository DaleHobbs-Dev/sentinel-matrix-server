"""Admin for the sentinelapi application."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from sentinelapi.models import Instructor, User, Student, Course

admin.site.register(Instructor)
admin.site.register(Student)
admin.site.register(Course)


@admin.register(User)
class EmailUserAdmin(UserAdmin):
    """Adapt Django's user admin screens to the email-only user model."""

    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )


# Register your models here.
