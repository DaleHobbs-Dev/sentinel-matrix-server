"""Shared student metric calculations."""

from decimal import Decimal

from sentinelapi.constants import (
    ASSESSMENT_TYPE_ATTENDANCE,
    PRIOR_ACADEMIC_STANDING_SCORES,
)


class StudentMetricCalculator:
    """Calculate student metrics from a scoped StudentAssessment queryset."""

    def __init__(self, assessments, prior_academic_standing):
        self.assessments = assessments
        self.prior_academic_standing = prior_academic_standing

    def _get_academic_assessments(self):
        """Get all non-attendance-type StudentAssessments in this scope."""
        return self.assessments.exclude(
            assessment__course_assessment_type__assessment_type__name__iexact=ASSESSMENT_TYPE_ATTENDANCE
        )

    def _get_attendance_assessments(self):
        """Get all attendance-type StudentAssessments in this scope."""
        return self.assessments.filter(
            assessment__course_assessment_type__assessment_type__name__iexact=ASSESSMENT_TYPE_ATTENDANCE
        )

    # Method to calculate grade average.
    # As a property, it can be accessed like an attribute (so no need to call it like a method)
    @property
    def grade_average(self):
        """Average score across all graded academic assessments in this scope."""

        # Retrieve all academic assessments that have a score
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
        """Average attendance score in this scope."""

        # Retrieve all attendance assessments that have a score
        graded = self._get_attendance_assessments().filter(score__isnull=False)

        if not graded.exists():
            return None

        total_score = sum(sa.score for sa in graded)
        count = graded.count()

        return round(total_score / count, 2)

    @property
    def missing_assignment_rate(self):
        """Percentage of academic assessments marked missing in this scope."""
        academic = self._get_academic_assessments()
        total = academic.count()

        if total == 0:
            return None

        missing_count = academic.filter(is_missing=True).count()

        return round((Decimal(missing_count) / Decimal(total)) * 100, 2)

    @property
    def assignment_completion_rate(self):
        """Inverse of missing_assignment_rate."""
        missing_assignment_rate = self.missing_assignment_rate

        if missing_assignment_rate is None:
            return None

        return round(100 - missing_assignment_rate, 2)

    @property
    def risk_score(self):
        """Weighted composite score out of 100 in this scope."""
        grade_avg = self.grade_average
        attendance = self.attendance_rate
        completion = self.assignment_completion_rate
        prior_standing = PRIOR_ACADEMIC_STANDING_SCORES.get(
            self.prior_academic_standing
        )

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
        """Categorize the risk score into a band."""
        score = self.risk_score

        if score is None:
            return None

        if score >= 70:
            return "Low Risk"
        elif score >= 40:
            return "Moderate Risk"
        else:
            return "High Risk"
