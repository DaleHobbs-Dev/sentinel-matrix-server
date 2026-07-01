"""Model for CourseAssessmentType - Defining types of assessments for courses"""

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from .assessment_type import AssessmentType


class CourseAssessmentType(models.Model):
    """Configuration of an assessment type within a course."""

    course = models.ForeignKey(
        "sentinelapi.Course",
        on_delete=models.CASCADE,
        related_name="assessment_types_for_course",
    )
    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.CASCADE,
        related_name="courses_with_assessment_type",
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    risk_score_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["course", "assessment_type"],
                name="unique_assessment_type_per_course",
            )
        ]
