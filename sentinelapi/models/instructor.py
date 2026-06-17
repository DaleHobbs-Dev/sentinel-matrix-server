"""Model for Instructors"""

from django.db import models
from django.contrib.auth.models import User


class Instructor(models.Model):
    """Represents an instructor in the application"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
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
