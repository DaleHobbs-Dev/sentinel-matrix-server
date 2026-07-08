"""Views for handling student-related API endpoints"""

from django.db.models import Q
from rest_framework import permissions, serializers, viewsets, response, status

from sentinelapi.models import Student, Course


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model"""

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


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for the Student model."""

    current_courses = serializers.SerializerMethodField()

    def get_current_courses(self, obj):
        """Get the courses the student is currently enrolled in."""
        courses = [
            enrollment.course
            for enrollment in obj.enrollments.all()
            if enrollment.course.is_active
        ]

        return CourseSerializer(courses, many=True, context=self.context).data

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
        )


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
