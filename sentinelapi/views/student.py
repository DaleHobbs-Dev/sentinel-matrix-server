"""Views for Student related actions/methods.

Methods allowed by this ViewSet:
    list   -- Lists all students, optionally filtered by a search query; requires auth.
    retrieve   -- Retrieves a specific student by ID; requires auth.
"""

from django.db.models import Q
from rest_framework import permissions, viewsets, response, status
from sentinelapi.models import Student
from sentinelapi.serializers import StudentSerializer


class StudentViewSet(viewsets.ViewSet):
    """API endpoint for retrieving student information."""

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """List all students, optionally filtered by a search query."""

        search = request.query_params.get("search", "").strip()
        students = (
            Student.objects.prefetch_related("enrollments__course")
            .all()
            .order_by("last_name", "first_name")
        )

        if search:
            students = students.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(student_id__icontains=search)
                | Q(email__icontains=search)
            )

        serializer = StudentSerializer(students, many=True)
        return response.Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Retrieve a specific student by ID."""

        try:
            student = Student.objects.prefetch_related("enrollments__course").get(pk=pk)
            serializer = StudentSerializer(student, context={"request": request})
            return response.Response(serializer.data, status=status.HTTP_200_OK)
        except Student.DoesNotExist:
            return response.Response(
                {"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND
            )
