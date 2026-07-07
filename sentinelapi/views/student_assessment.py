"""Views for handling student assessment-related API endpoints"""

from rest_framework import viewsets, permissions, status, serializers, response
from sentinelapi.models import StudentAssessment


class StudentAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for StudentAssessment model"""

    class Meta:
        model = StudentAssessment
        fields = [
            "id",
            "enrollment",
            "assessment",
            "score",
            "is_missing",
            "completed_date",
            # "is_archived",  # Uncomment when soft delete is implemented
        ]
        read_only_fields = [
            "id",
        ]


class StudentAssessmentViewSet(viewsets.ViewSet):
    """ViewSet for handling StudentAssessment CRUD operations."""

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """Handle GET requests to list student assessments.

        Optional query params:
            - enrollment_id: filter by a specific enrollment
            - assessment_id: filter by a specific assessment
        """

        student_assessments = StudentAssessment.objects.all()

        enrollment_id = request.query_params.get("enrollment_id", None)
        if enrollment_id is not None:
            student_assessments = student_assessments.filter(
                enrollment__id=enrollment_id
            )

        assessment_id = request.query_params.get("assessment_id", None)
        if assessment_id is not None:
            student_assessments = student_assessments.filter(
                assessment__id=assessment_id
            )

        serializer = StudentAssessmentSerializer(student_assessments, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Handle GET requests for a single student assessment by its primary key (pk)."""
        try:
            student_assessment = StudentAssessment.objects.get(pk=pk)
            serializer = StudentAssessmentSerializer(student_assessment)
            return response.Response(serializer.data, status=status.HTTP_200_OK)
        except StudentAssessment.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        """Handle POST requests to create a new student assessment."""

        serializer = StudentAssessmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        """Handle PUT requests to fully update a student assessment."""
        try:
            student_assessment = StudentAssessment.objects.get(pk=pk)

            serializer = StudentAssessmentSerializer(
                student_assessment, data=request.data
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return response.Response(serializer.data, status=status.HTTP_200_OK)

        except StudentAssessment.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, pk=None):
        """Handle PATCH requests to partially update a student assessment."""
        try:
            student_assessment = StudentAssessment.objects.get(pk=pk)

            serializer = StudentAssessmentSerializer(
                student_assessment, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return response.Response(serializer.data, status=status.HTTP_200_OK)

        except StudentAssessment.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """Handle DELETE requests to remove a student assessment.

        Note: This is a hard delete for now. To implement soft delete later:
            1. Add is_archived = models.BooleanField(default=False) to the model
            2. Run migrations
            3. Replace the hard delete below with:
                student_assessment.is_archived = True
                student_assessment.save()
                return response.Response(status=status.HTTP_200_OK)
            4. Update the list method to filter out archived records by default:
                student_assessments = StudentAssessment.objects.filter(is_archived=False)
        """
        try:
            student_assessment = StudentAssessment.objects.get(pk=pk)
            student_assessment.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        except StudentAssessment.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
