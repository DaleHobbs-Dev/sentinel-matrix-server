"""Model for Course"""

from django.db import models
from django.conf import settings


class Course(models.Model):
    """Model for Course"""

    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course_name = models.CharField(max_length=100)
    description = models.TextField()
    term = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    course_image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """String representation of the Course model"""
        return (
            f"{self.course_name} - {self.term} (Instructor: {self.instructor.username})"
        )
