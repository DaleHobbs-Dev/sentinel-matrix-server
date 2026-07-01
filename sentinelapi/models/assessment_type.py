"""Model for AssessmentType - Defining Global types of assessments for courses"""

from django.db import models


class AssessmentType(models.Model):
    """Global assessment category, such as Attendance or Exams."""

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.name}"
