"""Serializers for Course Related Models"""

from rest_framework import serializers
from sentinelapi.models import Course, Enrollment, Instructor
from sentinelapi.services.number_helpers import _decimal_to_float


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model"""

    is_instructor = serializers.SerializerMethodField()

    # returns True if the current user is the instructor of the course, otherwise False
    def get_is_instructor(self, obj):
        """Check if the current user is the instructor of the course"""
        return self.context["request"].user == obj.instructor.user

    class Meta:
        model = Course
        fields = [
            "id",
            "instructor",
            "course_name",
            "description",
            "term",
            "course_image_url",
            "created_at",
            "updated_at",
            "is_instructor",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "instructor",
            "created_at",
            "updated_at",
            "is_instructor",
        ]


class CourseDashboardStudentSerializer(serializers.Serializer):
    """Serializer for a student's course-specific dashboard metrics."""

    id = serializers.IntegerField(source="student.id", read_only=True)
    enrollment_id = serializers.IntegerField(source="id", read_only=True)
    student_id = serializers.CharField(source="student.student_id", read_only=True)
    first_name = serializers.CharField(source="student.first_name", read_only=True)
    last_name = serializers.CharField(source="student.last_name", read_only=True)
    grade_average = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()
    missing_assignment_count = serializers.SerializerMethodField()
    risk_score = serializers.SerializerMethodField()
    risk_band = serializers.ReadOnlyField()

    def get_grade_average(self, obj):
        """Get the grade average of the student associated with the enrollment."""
        return _decimal_to_float(obj.grade_average)

    def get_attendance_rate(self, obj):
        """Get the attendance rate of the student associated with the enrollment."""
        return _decimal_to_float(obj.attendance_rate)

    def get_missing_assignment_count(self, obj):
        """Get the count of missing assignments for the student associated with the enrollment."""
        return obj._get_academic_assessments().filter(is_missing=True).count()

    def get_risk_score(self, obj):
        """Get the enrollment's risk score."""
        return _decimal_to_float(obj.risk_score)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "enrollment_id",
            "student_id",
            "first_name",
            "last_name",
            "grade_average",
            "attendance_rate",
            "missing_assignment_count",
            "risk_score",
            "risk_band",
        ]


class CourseDashboardMetricsSerializer(serializers.Serializer):
    """Serialize aggregated course dashboard metrics."""

    average_grade = serializers.FloatField(allow_null=True)
    attendance_rate = serializers.FloatField(allow_null=True)
    high_risk_student_count = serializers.IntegerField()
    moderate_risk_student_count = serializers.IntegerField()

    class Meta:
        fields = [
            "average_grade",
            "attendance_rate",
            "high_risk_student_count",
            "moderate_risk_student_count",
        ]


class CourseDashboardSerializer(serializers.Serializer):
    """Serializer for the course dashboard endpoint."""

    id = serializers.IntegerField()
    course_name = serializers.CharField()
    description = serializers.CharField()
    metrics = CourseDashboardMetricsSerializer()
    students = CourseDashboardStudentSerializer(many=True)

    class Meta:
        fields = [
            "id",
            "course_name",
            "description",
            "metrics",
            "students",
        ]


class InstructorDashboardRiskStudentSerializer(serializers.Serializer):
    """Serialize at-risk enrollment details for the instructor dashboard."""

    id = serializers.IntegerField(source="student.id", read_only=True)
    student_id = serializers.CharField(source="student.student_id", read_only=True)
    enrollment_id = serializers.IntegerField(source="id", read_only=True)
    full_name = serializers.CharField(source="student.full_name", read_only=True)
    course_id = serializers.IntegerField(source="course.id", read_only=True)
    course = serializers.CharField(source="course.course_name", read_only=True)
    risk_score = serializers.SerializerMethodField()
    risk_band = serializers.ReadOnlyField()

    def get_risk_score(self, obj):
        """Get the enrollment's risk score."""
        return _decimal_to_float(obj.risk_score)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student_id",
            "enrollment_id",
            "course_id",
            "full_name",
            "course",
            "risk_score",
            "risk_band",
        ]


class InstructorDashboardSerializer(serializers.Serializer):
    """Serializer for the instructor's primary dashboard."""

    total_course_count = serializers.IntegerField()
    total_student_count = serializers.IntegerField()
    high_risk_student_count = serializers.IntegerField()
    moderate_risk_student_count = serializers.IntegerField()
    risk_students = InstructorDashboardRiskStudentSerializer(many=True)

    class Meta:
        model = Instructor
        fields = [
            "total_course_count",
            "total_student_count",
            "high_risk_student_count",
            "moderate_risk_student_count",
            "risk_students",
        ]
