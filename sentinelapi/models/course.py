"""Model for Course"""

from django.db import models


class Course(models.Model):
    """Model for Course"""

    instructor = models.ForeignKey(
        "sentinelapi.Instructor", on_delete=models.CASCADE, related_name="courses"
    )
    course_name = models.CharField(max_length=100)
    description = models.TextField()
    term = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    course_image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """String representation of the Course model"""
        return f"{self.course_name} - {self.term} (Instructor: {self.instructor.user.first_name} {self.instructor.user.last_name})"
