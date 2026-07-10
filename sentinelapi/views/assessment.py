"""Views for handling assessment-related API requests."""

from django.db import IntegrityError
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from sentinelapi.models import Assessment
from sentinelapi.serializers import AssessmentSerializer


class AssessmentViewSet(viewsets.ViewSet):
    """Handle CRUD operations for assessments owned by an instructor."""

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """List the instructor's assessments with optional filters."""
        course_id = request.query_params.get("course_id")
        assessment_type_id = request.query_params.get("assessment_type_id")

        filters = Q(course_assessment_type__course__instructor__user=request.user)
        if course_id:
            filters &= Q(course_assessment_type__course_id=course_id)
        if assessment_type_id:
            filters &= Q(course_assessment_type__assessment_type_id=assessment_type_id)

        assessments = Assessment.objects.filter(filters).select_related(
            "course_assessment_type",
            "course_assessment_type__course",
            "course_assessment_type__assessment_type",
        )

        serializer = AssessmentSerializer(
            assessments, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Retrieve one assessment owned by the instructor."""
        try:
            assessment = Assessment.objects.get(
                pk=pk,
                course_assessment_type__course__instructor__user=request.user,
            )
        except Assessment.DoesNotExist:
            return Response(
                {"detail": "Assessment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AssessmentSerializer(assessment, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """Create an assessment for one of the instructor's courses."""
        serializer = AssessmentSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            serializer.save()
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "An assessment with this title already exists for "
                        "the given course assessment type."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        """Replace an assessment owned by the instructor."""
        return self._update(request, pk, partial=False)

    def partial_update(self, request, pk=None):
        """Partially update an assessment owned by the instructor."""
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        try:
            assessment = Assessment.objects.get(
                pk=pk,
                course_assessment_type__course__instructor__user=request.user,
            )
        except Assessment.DoesNotExist:
            return Response(
                {"detail": "Assessment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AssessmentSerializer(
            assessment,
            data=request.data,
            partial=partial,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        try:
            serializer.save()
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "An assessment with this title already exists for "
                        "the given course assessment type."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        """Delete an assessment owned by the instructor."""
        try:
            assessment = Assessment.objects.get(
                pk=pk,
                course_assessment_type__course__instructor__user=request.user,
            )
        except Assessment.DoesNotExist:
            return Response(
                {"detail": "Assessment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        assessment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
