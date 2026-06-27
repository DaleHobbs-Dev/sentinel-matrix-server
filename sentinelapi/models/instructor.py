"""Model for Instructors"""

from django.conf import settings
from django.db import models


class Instructor(models.Model):
    """Represents an instructor in the application"""

    # Referencing AUTH_USER_MODEL keeps this relationship compatible with the
    # custom user model configured in settings.py.
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.URLField(blank=True, null=True)
    subject_taught = models.TextField(blank=True, null=True)
    university = models.TextField(blank=True, null=True)

    def __str__(self):
        """
        Return a string representation of the instructor

        This is useful for displaying the instructor's information in the Django admin interface
        and other contexts where a string representation is needed.
        """

        return f"{self.user.get_full_name()} - {self.subject_taught}"
