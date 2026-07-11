"""Model for CourseAssessmentType - Defining types of assessments for courses"""

from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from sentinelapi.constants import ASSESSMENT_TYPE_ATTENDANCE
from .assessment_type import AssessmentType


class CourseAssessmentType(models.Model):
    """Configuration of an assessment type within a course."""

    ATTENDANCE_RISK_SCORE_WEIGHT = Decimal("30.00")
    ACADEMIC_RISK_SCORE_WEIGHT = Decimal("40.00")

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

    @classmethod
    def fixed_risk_score_weight_for(cls, assessment_type_name):
        """Return the MVP risk score weight for an assessment type name."""
        if assessment_type_name.lower() == ASSESSMENT_TYPE_ATTENDANCE:
            return cls.ATTENDANCE_RISK_SCORE_WEIGHT

        return cls.ACADEMIC_RISK_SCORE_WEIGHT

    def save(self, *args, **kwargs):
        """Keep risk score weighting fixed to the MVP risk formula."""
        self.risk_score_weight = self.fixed_risk_score_weight_for(
            self.assessment_type.name
        )
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {
                "risk_score_weight"
            }
        super().save(*args, **kwargs)
