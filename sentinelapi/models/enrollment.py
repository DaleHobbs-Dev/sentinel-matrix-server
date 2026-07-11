"""Model for Enrollment - Connecting Students to Courses"""

from django.db import models
from .course import Course
from .student import Student
from sentinelapi.constants import ASSESSMENT_TYPE_ATTENDANCE
from sentinelapi.services.student_metrics import StudentMetricCalculator


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
            assessment__course_assessment_type__assessment_type__name__iexact=ASSESSMENT_TYPE_ATTENDANCE
        )

    def _get_attendance_assessments(self):
        """Helper function to get all attendance-type StudentAssessments"""
        return self.student_assessments.filter(
            assessment__course_assessment_type__assessment_type__name__iexact=ASSESSMENT_TYPE_ATTENDANCE
        )

    @property
    def prior_academic_standing(self):
        """Student's prior academic standing for this enrollment."""
        return self.student.prior_academic_standing

    def _metric_calculator(self):
        """Get the metric calculator scoped to this enrollment's assessments."""
        return StudentMetricCalculator(
            self.student_assessments.all(),
            self.prior_academic_standing,
        )

    @property
    def grade_average(self):
        """Average score across all non-attendance assessments that have been graded.

        Only includes completed assessments (score is not null).
        Returns None if no graded academic assessments exist yet.
        """
        return self._metric_calculator().grade_average

    @property
    def attendance_rate(self):
        """Average score across all attendance-type assessments that have been graded.

        Attendance assessments are recorded on a 0-100 scale so we average
        the scores directly.
        Returns None if no graded attendance assessments exist yet.
        """
        return self._metric_calculator().attendance_rate

    @property
    def missing_assignment_rate(self):
        """Percentage of non-attendance assessments marked as missing.

        Returns None if no academic assessments exist yet.
        """
        return self._metric_calculator().missing_assignment_rate

    @property
    def assignment_completion_rate(self):
        """Inverse of missing_assignment_rate — used in the risk score formula.

        Returns None if missing_assignment_rate is None.
        """
        return self._metric_calculator().assignment_completion_rate

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
        return self._metric_calculator().risk_score

    @property
    def risk_band(self):
        """Categorize the risk score into a band.

        Returns None if risk_score is not yet calculable.
        """
        return self._metric_calculator().risk_band
