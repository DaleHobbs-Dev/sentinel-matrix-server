"""Model for Assessment - Defining assessments for courses"""

from django.db import models
from .course_assessment_type import CourseAssessmentType


class Assessment(models.Model):
    """Represents an assessment within a course."""

    course_assessment_type = models.ForeignKey(
        CourseAssessmentType,
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    title = models.CharField(max_length=100)
    max_score = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["course_assessment_type", "title"],
                name="unique_assessment_title_per_course_assessment_type",
            )
        ]

    def __str__(self):
        return f"{self.title} - {self.course_assessment_type.course.course_name}"
