"""Views for handling course-related API endpoints"""

from rest_framework import viewsets, permissions, status, serializers, response
from django.db.models import Q
from sentinelapi.models import Course


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model"""

    is_instructor = serializers.SerializerMethodField()

    # returns True if the current user is the instructor of the course, otherwise False
    def get_is_instructor(self, obj):
        """Check if the current user is the instructor of the course"""
        return self.context["request"].user == obj.instructor

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


class CourseViewSet(viewsets.ViewSet):
    """ViewSet for handling Course CRUD operations."""

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """Handle GET requests to list all Courses."""

        search = request.query_params.get("search", None)
        courses = Course.objects.all()

        if search:
            courses = courses.filter(
                Q(course_name__icontains=search)
                | Q(description__icontains=search)
                | Q(instructor__username__icontains=search)
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

    def create(self, request):
        """Handle POST requests to create a new course."""

        serializer = CourseSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(instructor=request.user)

        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        """Handle DELETE requests for a single course by its primary key (pk)."""
        try:
            course = Course.objects.get(pk=pk)

            # Only allow the owner of the course to delete it
            if course.instructor != request.user:
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
            if course.instructor != request.user:
                return response.Response(status=status.HTTP_403_FORBIDDEN)

            serializer = CourseSerializer(
                course, data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(instructor=request.user)
            return response.Response(serializer.data, status=status.HTTP_200_OK)

        except Course.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, pk=None):
        """Handle PATCH requests to partially update a single course by its primary key (pk)."""
        try:
            course = Course.objects.get(pk=pk)

            # Only allow the owner of the course to partially update it
            if course.instructor != request.user:
                return response.Response(status=status.HTTP_403_FORBIDDEN)

            serializer = CourseSerializer(
                course, data=request.data, partial=True, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(instructor=request.user)
            return response.Response(serializer.data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
