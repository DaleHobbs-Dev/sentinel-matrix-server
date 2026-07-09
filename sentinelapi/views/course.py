"""Views for handling course-related API endpoints"""

from rest_framework import viewsets, permissions, status, serializers, response
from rest_framework.decorators import action
from django.db import transaction
from django.db.models import Prefetch, Q
from sentinelapi.models import Course, Enrollment
from sentinelapi.services.course_assessment_types import (
    create_default_course_assessment_types,
)


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

    id = serializers.SerializerMethodField()
    student_id = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    grade_average = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()
    missing_assignment_count = serializers.SerializerMethodField()
    risk_band = serializers.SerializerMethodField()

    def get_id(self, obj):
        """Get the ID of the student associated with the enrollment."""
        return obj.student.id

    def get_student_id(self, obj):
        """Get the student ID of the student associated with the enrollment."""
        return obj.student.student_id

    def get_first_name(self, obj):
        """Get the first name of the student associated with the enrollment."""
        return obj.student.first_name

    def get_last_name(self, obj):
        """Get the last name of the student associated with the enrollment."""
        return obj.student.last_name

    def get_grade_average(self, obj):
        """Get the grade average of the student associated with the enrollment."""
        return _decimal_to_float(obj.grade_average)

    def get_attendance_rate(self, obj):
        """Get the attendance rate of the student associated with the enrollment."""
        return _decimal_to_float(obj.attendance_rate)

    def get_missing_assignment_count(self, obj):
        """Get the count of missing assignments for the student associated with the enrollment."""
        return obj._get_academic_assessments().filter(is_missing=True).count()

    def get_risk_band(self, obj):
        """Get the risk band of the student associated with the enrollment."""
        return obj.risk_band


class CourseDashboardSerializer(serializers.ModelSerializer):
    """Serializer for the course dashboard endpoint."""

    metrics = serializers.SerializerMethodField()
    students = serializers.SerializerMethodField()

    def get_metrics(self, obj):
        """Get the aggregated metrics for the course dashboard."""
        enrollments = list(obj.enrollments.all())
        grade_values = []
        attendance_values = []

        for enrollment in enrollments:
            grade_average = enrollment.grade_average
            attendance_rate = enrollment.attendance_rate

            if grade_average is not None:
                grade_values.append(grade_average)

            if attendance_rate is not None:
                attendance_values.append(attendance_rate)

        return {
            "average_grade": _average_decimal_values(grade_values),
            "attendance_rate": _average_decimal_values(attendance_values),
            "high_risk_student_count": sum(
                1 for enrollment in enrollments if enrollment.risk_band == "High Risk"
            ),
            "moderate_risk_student_count": sum(
                1
                for enrollment in enrollments
                if enrollment.risk_band == "Moderate Risk"
            ),
        }

    def get_students(self, obj):
        """Get the list of students enrolled in the course."""
        enrollments = obj.enrollments.all()
        serializer = CourseDashboardStudentSerializer(enrollments, many=True)
        return serializer.data

    class Meta:
        model = Course
        fields = [
            "id",
            "course_name",
            "description",
            "metrics",
            "students",
        ]


def _decimal_to_float(value):
    """Convert Decimal-like computed values into JSON-friendly numbers."""
    if value is None:
        return None

    return float(value)


def _average_decimal_values(values):
    """Average Decimal values, returning None when no values are available."""
    if not values:
        return None

    return float(round(sum(values) / len(values), 2))


class CourseViewSet(viewsets.ViewSet):
    """ViewSet for handling Course CRUD operations."""

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """Handle GET requests to list all requesting Instructor's Courses."""

        courses = Course.objects.all().filter(instructor__user=request.user)

        active_param = request.query_params.get("is_active", None)
        if active_param is not None:
            courses = courses.filter(is_active=active_param.lower() == "true")

        search = request.query_params.get("search", None)

        if search:
            courses = courses.filter(
                Q(course_name__icontains=search)
                | Q(description__icontains=search)
                | Q(instructor__user__email__icontains=search)
                | Q(instructor__user__first_name__icontains=search)
                | Q(instructor__user__last_name__icontains=search)
            )

        serializer = CourseSerializer(courses, many=True, context={"request": request})

        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Handle GET requests for a single course by its primary key (pk)."""
        try:
            course = Course.objects.get(pk=pk)
            serializer = CourseSerializer(course, context={"request": request})
            return response.Response(serializer.data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["get"], url_path="dashboard")
    def dashboard(self, request, pk=None):
        """Handle GET requests for a course dashboard."""
        try:
            course = Course.objects.prefetch_related(
                Prefetch(
                    "enrollments",
                    queryset=Enrollment.objects.select_related("student")
                    .prefetch_related(
                        "student_assessments__assessment__course_assessment_type__assessment_type"
                    )
                    .order_by("student__last_name", "student__first_name"),
                ),
            ).get(pk=pk)
            serializer = CourseDashboardSerializer(course)
            return response.Response(serializer.data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        """Handle POST requests to create a new course."""

        serializer = CourseSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            course = serializer.save(instructor=request.user.instructor)
            create_default_course_assessment_types(course)

        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        """Handle DELETE requests for a single course by its primary key (pk)."""
        try:
            course = Course.objects.get(pk=pk)

            # Only allow the owner of the course to delete it
            if course.instructor.user != request.user:
                return response.Response(status=status.HTTP_403_FORBIDDEN)

            course.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        except Course.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)

    def update(self, request, pk=None):
        """Handle PUT requests to update a single course by its primary key (pk)."""
        try:
            course = Course.objects.get(pk=pk)

            # Only allow the owner of the course to update it
            if course.instructor.user != request.user:
                return response.Response(status=status.HTTP_403_FORBIDDEN)

            serializer = CourseSerializer(
                course, data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(instructor=request.user.instructor)
            return response.Response(serializer.data, status=status.HTTP_200_OK)

        except Course.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, pk=None):
        """Handle PATCH requests to partially update a single course by its primary key (pk)."""
        try:
            course = Course.objects.get(pk=pk)

            # Only allow the owner of the course to partially update it
            if course.instructor.user != request.user:
                return response.Response(status=status.HTTP_403_FORBIDDEN)

            serializer = CourseSerializer(
                course, data=request.data, partial=True, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(instructor=request.user.instructor)
            return response.Response(serializer.data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
