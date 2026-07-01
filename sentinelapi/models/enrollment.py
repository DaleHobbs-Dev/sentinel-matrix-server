"""Model for Enrollment - Connecting Students to Courses"""

from django.db import models
from .course import Course
from .student import Student


class Enrollment(models.Model):
    """Model for Enrollment - Connecting Students to Courses"""

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course")

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} enrolled in {self.course.course_name}"
