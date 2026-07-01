"""Model for StudentAssessment - Connecting Student Enrollments to Assessments"""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from .enrollment import Enrollment
from .assessment import Assessment


class StudentAssessment(models.Model):
    """Represents a student's assessment within a course."""

    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="student_assessments"
    )
    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="student_assessments"
    )
    score = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    is_missing = models.BooleanField(default=False)

    def clean(self):
        """
        Custom validation to ensure that the assessment and enrollment belong to the same course.
        """
        super().clean()

        if self.enrollment_id and self.assessment_id:
            enrollment_course_id = self.enrollment.course_id
            assessment_course_id = self.assessment.course_assessment_type.course_id

            if enrollment_course_id != assessment_course_id:
                raise ValidationError(
                    {
                        "assessment": (
                            "The assessment and enrollment must belong "
                            "to the same course."
                        )
                    }
                )

    class Meta:
        """Meta class for StudentAssessment model."""

        constraints = [
            models.UniqueConstraint(
                fields=["enrollment", "assessment"], name="unique_enrollment_assessment"
            ),
            # Constraint checks to ensure valid states for StudentAssessment
            models.CheckConstraint(
                condition=(
                    # Pending assessments must have a score and completed_date as null
                    Q(
                        is_missing=False,
                        score__isnull=True,
                        completed_date__isnull=True,
                    )
                    |
                    # Completed assessments must have a score and completed_date not null
                    Q(
                        is_missing=False,
                        score__isnull=False,
                        completed_date__isnull=False,
                    )
                    |
                    # Missing assessments must have a score and completed_date as null
                    Q(
                        is_missing=True,
                        score__isnull=True,
                        completed_date__isnull=True,
                    )
                ),
                name="valid_student_assessment_state",
            ),
        ]

    def __str__(self):
        return f"{self.enrollment.student.first_name} {self.enrollment.student.last_name} - {self.assessment.title}"
