"""Model for Students"""

from decimal import Decimal

from django.apps import apps
from django.db import models


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

    # Academic Standing class with choices for "Good" and "At Risk"
    class AcademicStanding(models.TextChoices):
        """Choices for Academic Standing of Students"""

        GOOD = "good", "Good"
        AT_RISK = "at risk", "At Risk"

    prior_academic_standing = models.CharField(
        max_length=100,
        choices=AcademicStanding.choices,
        default=AcademicStanding.GOOD,
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def _get_student_assessments(self):
        """Get all StudentAssessments attached to this student's enrollments."""
        StudentAssessment = apps.get_model("sentinelapi", "StudentAssessment")
        return StudentAssessment.objects.filter(enrollment__student=self)

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

    @property
    def grade_average(self):
        """Average score across all graded academic assessments in all courses."""
        graded = self._get_academic_assessments().filter(score__isnull=False)

        if not graded.exists():
            return None

        total_score = sum(sa.score for sa in graded)
        total_possible = sum(sa.assessment.max_score for sa in graded)

        if total_possible == 0:
            return None

        return round((total_score / total_possible) * 100, 2)

    @property
    def attendance_rate(self):
        """Average attendance score across all enrolled courses."""
        graded = self._get_attendance_assessments().filter(score__isnull=False)

        if not graded.exists():
            return None

        total_score = sum(sa.score for sa in graded)
        count = graded.count()

        return round(total_score / count, 2)

    @property
    def missing_assignment_rate(self):
        """Percentage of academic assessments marked missing across all courses."""
        academic = self._get_academic_assessments()
        total = academic.count()

        if total == 0:
            return None

        missing_count = academic.filter(is_missing=True).count()

        return round((Decimal(missing_count) / Decimal(total)) * 100, 2)

    @property
    def assignment_completion_rate(self):
        """Inverse of missing_assignment_rate."""
        if self.missing_assignment_rate is None:
            return None

        return round(100 - self.missing_assignment_rate, 2)

    @property
    def risk_score(self):
        """Weighted composite score out of 100 across all enrolled courses."""
        grade_avg = self.grade_average
        attendance = self.attendance_rate
        completion = self.assignment_completion_rate
        prior_standing = PRIOR_ACADEMIC_STANDING.get(self.prior_academic_standing)

        if (
            grade_avg is None
            or attendance is None
            or completion is None
            or prior_standing is None
        ):
            return None

        score = (
            (grade_avg * Decimal("0.40"))
            + (attendance * Decimal("0.30"))
            + (completion * Decimal("0.20"))
            + (prior_standing * Decimal("0.10"))
        )

        return round(score, 2)

    @property
    def risk_band(self):
        """Categorize the student-level risk score into a band."""
        score = self.risk_score

        if score is None:
            return None

        if score >= 70:
            return "Low Risk"
        elif score >= 40:
            return "Moderate Risk"
        else:
            return "High Risk"

    # Meta class for additional model options
    class Meta:
        """
        Ensure that the prior_academic_standing field
        can only have values of 'good' or 'at risk'
        """

        constraints = [
            models.CheckConstraint(
                condition=models.Q(prior_academic_standing__in=["good", "at risk"]),
                name="valid_prior_academic_standing",
            ),
        ]


PRIOR_ACADEMIC_STANDING = {
    Student.AcademicStanding.GOOD: Decimal("90"),
    Student.AcademicStanding.AT_RISK: Decimal("60"),
}
