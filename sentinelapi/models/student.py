"""Model for Students"""

from django.apps import apps
from django.db import models

from sentinelapi.constants import (
    ACADEMIC_STANDING_AVERAGE,
    ACADEMIC_STANDING_CHOICES,
    ACADEMIC_STANDING_EXCELLENT,
    ACADEMIC_STANDING_GREAT,
    ACADEMIC_STANDING_POOR,
    ACADEMIC_STANDING_VALUES,
    PRIOR_ACADEMIC_STANDING_SCORES,
)
from sentinelapi.services.student_metrics import StudentMetricCalculator


# Blueprint for the Student objects
# Student class inherits from Django's models.Model base class
# This provides built-in functionality for database operations.
class Student(models.Model):
    """Model for Students"""

    # Create instances of models.XXXField classes to define the fields of the Student model.
    # Each field corresponds to a column in the database table.
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    enrollment_date = models.DateField()

    # Academic Standing class with choices for "Excellent", "Great", "Average", and "Poor"
    class AcademicStanding(models.TextChoices):
        """Choices for Academic Standing of Students"""

        EXCELLENT = ACADEMIC_STANDING_EXCELLENT, "Excellent"
        GREAT = ACADEMIC_STANDING_GREAT, "Great"
        AVERAGE = ACADEMIC_STANDING_AVERAGE, "Average"
        POOR = ACADEMIC_STANDING_POOR, "Poor"

    prior_academic_standing = models.CharField(
        max_length=100,
        choices=ACADEMIC_STANDING_CHOICES,
        default=AcademicStanding.EXCELLENT,
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        """Return the student's display name."""
        return f"{self.first_name} {self.last_name}"

    def _get_student_assessments(self):
        """Get all StudentAssessments attached to this student's enrollments."""
        student_assessment = apps.get_model("sentinelapi", "StudentAssessment")
        return student_assessment.objects.filter(enrollment__student=self)

    def _get_academic_assessments(self):
        """Get all non-attendance-type StudentAssessments for this student."""
        return self._get_student_assessments().exclude(
            assessment__course_assessment_type__assessment_type__name__iexact="attendance"
        )

    def _get_attendance_assessments(self):
        """Get all attendance-type StudentAssessments for this student."""
        return self._get_student_assessments().filter(
            assessment__course_assessment_type__assessment_type__name__iexact="attendance"
        )

    def _metric_calculator(self):
        """Get the metric calculator scoped to all of this student's assessments."""
        return StudentMetricCalculator(
            self._get_student_assessments(),
            self.prior_academic_standing,
        )

    @property
    def grade_average(self):
        """Average score across all graded academic assessments in all courses."""
        return self._metric_calculator().grade_average

    @property
    def attendance_rate(self):
        """Average attendance score across all enrolled courses."""
        return self._metric_calculator().attendance_rate

    @property
    def missing_assignment_rate(self):
        """Percentage of academic assessments marked missing across all courses."""
        return self._metric_calculator().missing_assignment_rate

    @property
    def assignment_completion_rate(self):
        """Inverse of missing_assignment_rate."""
        return self._metric_calculator().assignment_completion_rate

    @property
    def risk_score(self):
        """Weighted composite score out of 100 across all enrolled courses."""
        return self._metric_calculator().risk_score

    @property
    def risk_band(self):
        """Categorize the student-level risk score into a band."""
        return self._metric_calculator().risk_band

    # Meta class for additional model options
    class Meta:
        """
        Ensure that the prior_academic_standing field
        can only have values of 'excellent', 'great', 'average', or 'poor'
        """

        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    prior_academic_standing__in=ACADEMIC_STANDING_VALUES
                ),
                name="valid_prior_academic_standing",
            ),
        ]


PRIOR_ACADEMIC_STANDING = PRIOR_ACADEMIC_STANDING_SCORES
