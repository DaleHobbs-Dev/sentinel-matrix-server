"""Model for Enrollment - Connecting Students to Courses"""

from decimal import Decimal

from django.db import models
from .course import Course
from .student import Student

PRIOR_ACADEMIC_STANDING = {
    Student.AcademicStanding.GOOD: Decimal("90"),
    Student.AcademicStanding.AT_RISK: Decimal("60"),
}


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

    # Helper function to split StudentAssessments by type
    def _get_academic_assessments(self):
        """Helper function to get all non-attendance-type StudentAssessments"""
        return self.student_assessments.exclude(
            assessment__course_assessment_type__assessment_type__name__iexact="attendance"
        )

    def _get_attendance_assessments(self):
        """Helper function to get all attendance-type StudentAssessments"""
        return self.student_assessments.filter(
            assessment__course_assessment_type__assessment_type__name__iexact="attendance"
        )

    @property
    def prior_academic_standing(self):
        """Student's prior academic standing for this enrollment."""
        return self.student.prior_academic_standing

    @property
    def grade_average(self):
        """Average score across all non-attendance assessments that have been graded.

        Only includes completed assessments (score is not null).
        Returns None if no graded academic assessments exist yet.
        """
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
        """Average score across all attendance-type assessments that have been graded.

        Attendance assessments are recorded on a 0-100 scale so we average
        the scores directly.
        Returns None if no graded attendance assessments exist yet.
        """
        graded = self._get_attendance_assessments().filter(score__isnull=False)

        if not graded.exists():
            return None

        total_score = sum(sa.score for sa in graded)
        count = graded.count()

        return round(total_score / count, 2)

    @property
    def missing_assignment_rate(self):
        """Percentage of non-attendance assessments marked as missing.

        Returns None if no academic assessments exist yet.
        """
        academic = self._get_academic_assessments()
        total = academic.count()

        if total == 0:
            return None

        missing_count = academic.filter(is_missing=True).count()

        return round((Decimal(missing_count) / Decimal(total)) * 100, 2)

    @property
    def assignment_completion_rate(self):
        """Inverse of missing_assignment_rate — used in the risk score formula.

        Returns None if missing_assignment_rate is None.
        """
        if self.missing_assignment_rate is None:
            return None

        return round(100 - self.missing_assignment_rate, 2)

    # -------------------------------------------------------------------------
    # Risk score and risk band
    # -------------------------------------------------------------------------

    @property
    def risk_score(self):
        """Weighted composite score out of 100. Higher = lower risk.

        Formula:
            (grade_average        * 0.40)
          + (attendance_rate      * 0.30)
          + (completion_rate      * 0.20)
          + (prior_standing_score * 0.10)

        Returns None if any of the four factors are unavailable yet.
        """
        grade_avg = self.grade_average
        attendance = self.attendance_rate
        completion = self.assignment_completion_rate
        prior_standing = PRIOR_ACADEMIC_STANDING.get(self.prior_academic_standing)

        # If any factor is missing we can't produce a meaningful score yet
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
        """Categorize the risk score into a band.

        Returns None if risk_score is not yet calculable.
        """
        score = self.risk_score

        if score is None:
            return None

        if score >= 70:
            return "Low Risk"
        elif score >= 40:
            return "Moderate Risk"
        else:
            return "High Risk"
