"""Serializers for Student Related Models"""

from rest_framework import serializers
from sentinelapi.models import Course, Student


class CourseSummarySerializer(serializers.ModelSerializer):
    """Serialize compact course details for nested responses."""

    class Meta:
        model = Course
        fields = [
            "id",
            "course_name",
            "is_active",
        ]
        read_only_fields = [
            "id",
        ]


class StudentSummarySerializer(serializers.ModelSerializer):
    """Serialize compact student details for nested responses."""

    class Meta:
        model = Student
        fields = [
            "id",
            "first_name",
            "last_name",
        ]
        read_only_fields = [
            "id",
        ]


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for the Student model."""

    current_courses = serializers.SerializerMethodField()
    grade_average = serializers.ReadOnlyField()
    attendance_rate = serializers.ReadOnlyField()
    missing_assignment_rate = serializers.ReadOnlyField()
    assignment_completion_rate = serializers.ReadOnlyField()
    risk_score = serializers.ReadOnlyField()
    risk_band = serializers.ReadOnlyField()

    def get_current_courses(self, obj):
        """Get the courses the student is currently enrolled in."""
        courses = [
            enrollment.course
            for enrollment in obj.enrollments.all()
            if enrollment.course.is_active
        ]

        return CourseSummarySerializer(courses, many=True, context=self.context).data

    class Meta:
        model = Student
        fields = (
            "id",
            "first_name",
            "last_name",
            "student_id",
            "email",
            "prior_academic_standing",
            "enrollment_date",
            "current_courses",
            "grade_average",
            "attendance_rate",
            "missing_assignment_rate",
            "assignment_completion_rate",
            "risk_score",
            "risk_band",
        )
