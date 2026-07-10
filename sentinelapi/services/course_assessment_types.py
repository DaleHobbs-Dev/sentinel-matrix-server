"""Helpers for course assessment type configuration."""

from decimal import Decimal

from sentinelapi.models import AssessmentType, CourseAssessmentType


DEFAULT_COURSE_ASSESSMENT_TYPES = (
    {
        "name": "Attendance",
        "weight": Decimal("20"),
    },
    {
        "name": "Homework",
        "weight": Decimal("80"),
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
            },
        )
