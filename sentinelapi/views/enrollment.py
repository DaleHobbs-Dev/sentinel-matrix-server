"""Views for handling enrollment-related API endpoints"""

from rest_framework import viewsets, permissions, status, response
from sentinelapi.models import Enrollment
from sentinelapi.serializers import EnrollmentSerializer


class EnrollmentViewSet(viewsets.ViewSet):
    """ViewSet for handling Enrollment operations."""

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """Handle GET requests to list enrollments.

        Optional query params:
            - student_id: filter enrollments by a specific student
            - course_id: filter enrollments by a specific course
        """

        enrollments = Enrollment.objects.select_related("student", "course").all()

        student_id = request.query_params.get("student_id", None)
        if student_id is not None:
            enrollments = enrollments.filter(student__id=student_id)

        course_id = request.query_params.get("course_id", None)
        if course_id is not None:
            enrollments = enrollments.filter(course__id=course_id)

        serializer = EnrollmentSerializer(enrollments, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """Handle POST requests to enroll a student into a course."""

        # First check that there isn't an existing enrollment for this student and course
        student_id = request.data.get("student")
        course_id = request.data.get("course")
        if Enrollment.objects.filter(
            student__id=student_id, course__id=course_id
        ).exists():
            return response.Response(
                {"detail": "Student is already enrolled in this course."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = EnrollmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        """Handle DELETE requests to remove a student from a course.

        Note: This is a hard delete for now. A soft delete (using an
        is_active flag) will be introduced in a future update so that
        assignment records tied to this enrollment are preserved.
        """

        try:
            enrollment = Enrollment.objects.get(pk=pk)
            enrollment.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        except Enrollment.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
