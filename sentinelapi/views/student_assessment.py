"""Views for Student Assessment related actions/methods.

Methods allowed by this ViewSet:
    list   -- Lists all student assessments, optionally filtered by enrollment or assessment; requires auth.
    retrieve   -- Retrieves a specific student assessment by ID; requires auth.
    create     -- Creates a new student assessment; requires auth.
    update     -- Fully updates an existing student assessment; requires auth.
    partial_update -- Partially updates an existing student assessment; requires auth.
    _update    -- Internal method to handle both full and partial updates of a student assessment; requires auth.
    destroy    -- Deletes a student assessment; requires auth.
"""

from rest_framework import viewsets, permissions, status, response
from sentinelapi.models import StudentAssessment
from sentinelapi.serializers import StudentAssessmentSerializer


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
        return self._update(request, pk, partial=False)

    def partial_update(self, request, pk=None):
        """Handle PATCH requests to partially update a student assessment."""
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        try:
            student_assessment = StudentAssessment.objects.get(pk=pk)

            serializer = StudentAssessmentSerializer(
                student_assessment, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return response.Response(serializer.data, status=status.HTTP_200_OK)

        except StudentAssessment.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """Handle DELETE requests to remove a student assessment.

        Note: This is a hard delete for now. I want to implement soft delete later
        """
        try:
            student_assessment = StudentAssessment.objects.get(pk=pk)
            student_assessment.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        except StudentAssessment.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
