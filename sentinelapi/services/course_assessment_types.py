"""Helpers for course assessment type configuration."""

from decimal import Decimal

from sentinelapi.models import AssessmentType, CourseAssessmentType


DEFAULT_COURSE_ASSESSMENT_TYPES = (
    {
        "name": "Attendance",
        "weight": Decimal("20"),
        "risk_score_weight": Decimal("60"),
    },
    {
        "name": "Homework",
        "weight": Decimal("80"),
        "risk_score_weight": Decimal("40"),
    },
)


def create_default_course_assessment_types(course):
    """Create the default assessment type configuration for a new course."""
    for config in DEFAULT_COURSE_ASSESSMENT_TYPES:
        assessment_type, _ = AssessmentType.objects.get_or_create(
            name=config["name"],
        )
        CourseAssessmentType.objects.get_or_create(
            course=course,
            assessment_type=assessment_type,
            defaults={
                "weight": config["weight"],
                "risk_score_weight": config["risk_score_weight"],
            },
        )
