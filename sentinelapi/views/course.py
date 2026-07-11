"""Views for Course related actions/methods.

Methods allowed by this ViewSet:
    list   -- Lists all courses for the requesting instructor, optionally filtered by active status and search query; requires auth.
    retrieve   -- Retrieves a specific course by ID; requires auth.
    create     -- Creates a new course; requires auth.
    update     -- Fully updates an existing course; requires auth.
    partial_update -- Partially updates an existing course; requires auth.
    _update    -- Internal method to handle both full and partial updates of a course; requires auth.
    destroy    -- Deletes a course; requires auth.
    dashboard  -- Retrieves the dashboard for a specific course; requires auth.
    instructor_dashboard -- Retrieves the main dashboard for platform; requires auth.
"""

from rest_framework import viewsets, permissions, status, response
from rest_framework.decorators import action
from django.db import transaction
from django.db.models import Prefetch, Q
from sentinelapi.models import Course, Enrollment
from sentinelapi.serializers import (
    CourseSerializer,
    CourseDashboardSerializer,
    InstructorDashboardSerializer,
)
from sentinelapi.services.course_assessment_types import (
    create_default_course_assessment_types,
)
from sentinelapi.services.course_dashboard import (
    build_course_dashboard,
    build_instructor_dashboard,
)


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
            serializer = CourseDashboardSerializer(build_course_dashboard(course))
            return response.Response(serializer.data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["get"], url_path="dashboard")
    def instructor_dashboard(self, request):
        """Handle GET requests for the instructor's primary dashboard."""
        if not hasattr(request.user, "instructor"):
            return response.Response(status=status.HTTP_403_FORBIDDEN)

        courses = list(
            Course.objects.filter(instructor=request.user.instructor)
            .prefetch_related(
                Prefetch(
                    "enrollments",
                    queryset=Enrollment.objects.select_related("student", "course")
                    .prefetch_related(
                        "student_assessments__assessment__course_assessment_type__assessment_type"
                    )
                    .order_by("student__last_name", "student__first_name"),
                ),
            )
            .order_by("course_name")
        )
        serializer = InstructorDashboardSerializer(build_instructor_dashboard(courses))
        return response.Response(serializer.data, status=status.HTTP_200_OK)

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
        return self._update(request, pk, partial=False)

    def partial_update(self, request, pk=None):
        """Handle PATCH requests to partially update a single course by its primary key (pk)."""
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        try:
            course = Course.objects.get(pk=pk)

            # Only allow the owner of the course to update it
            if course.instructor.user != request.user:
                return response.Response(status=status.HTTP_403_FORBIDDEN)

            serializer = CourseSerializer(
                course,
                data=request.data,
                partial=partial,
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(instructor=request.user.instructor)
            return response.Response(serializer.data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
