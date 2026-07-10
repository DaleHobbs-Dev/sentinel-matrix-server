"""Course dashboard aggregation helpers."""

from sentinelapi.services.number_helpers import (
    _average_decimal_values,
)


RISK_ORDER = {
    "High Risk": 0,
    "Moderate Risk": 1,
}


def build_course_dashboard(course):
    """Return serialized-ready course dashboard data."""
    enrollments = list(course.enrollments.all())
    return {
        "id": course.id,
        "course_name": course.course_name,
        "description": course.description,
        "metrics": build_course_metrics(enrollments),
        "students": enrollments,
    }


def build_course_metrics(enrollments):
    """Return aggregate metric data for a course's enrollments."""
    grade_values = []
    attendance_values = []

    for enrollment in enrollments:
        if enrollment.grade_average is not None:
            grade_values.append(enrollment.grade_average)

        if enrollment.attendance_rate is not None:
            attendance_values.append(enrollment.attendance_rate)

    return {
        "average_grade": _average_decimal_values(grade_values),
        "attendance_rate": _average_decimal_values(attendance_values),
        "high_risk_student_count": count_risk_enrollments(enrollments, "High Risk"),
        "moderate_risk_student_count": count_risk_enrollments(
            enrollments,
            "Moderate Risk",
        ),
    }


def build_instructor_dashboard(courses):
    """Return serialized-ready instructor dashboard data."""
    enrollments = get_course_enrollments(courses)
    return {
        "total_course_count": len(courses),
        "total_student_count": len(
            {enrollment.student_id for enrollment in enrollments}
        ),
        "high_risk_student_count": count_risk_enrollments(enrollments, "High Risk"),
        "moderate_risk_student_count": count_risk_enrollments(
            enrollments,
            "Moderate Risk",
        ),
        "risk_students": get_risk_enrollments(enrollments),
    }


def count_risk_enrollments(enrollments, risk_band):
    """Count enrollments that match a risk band."""
    return sum(1 for enrollment in enrollments if enrollment.risk_band == risk_band)


def get_course_enrollments(courses):
    """Flatten all enrollment records from a course list."""
    enrollments = []
    for course in courses:
        enrollments.extend(course.enrollments.all())
    return enrollments


def get_risk_enrollments(enrollments):
    """Return high and moderate risk enrollments, sorted by severity."""
    risk_enrollments = [
        enrollment for enrollment in enrollments if enrollment.risk_band in RISK_ORDER
    ]
    return sorted(
        risk_enrollments,
        key=lambda enrollment: (
            RISK_ORDER[enrollment.risk_band],
            enrollment.student.last_name,
            enrollment.student.first_name,
            enrollment.course.course_name,
        ),
    )
