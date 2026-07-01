"""Views for handling Assessment_Type related API requests"""

from rest_framework import permissions, viewsets, status, serializers
from rest_framework.response import Response

# import IntegrityError to handle unique constraint violation
# when a user tries to create multiple assessment types with the
# same name
from django.db import IntegrityError
from sentinelapi.models import AssessmentType


class AssessmentTypeSerializer(serializers.ModelSerializer):
    """Serializer for the AssessmentType model."""

    class Meta:
        model = AssessmentType
        fields = ["id", "name"]


class AssessmentTypeViewSet(viewsets.ViewSet):
    """ViewSet for handling Assessment_Type related API requests."""

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        List all assessment types.
        """
        assessment_types = AssessmentType.objects.all()
        serializer = AssessmentTypeSerializer(assessment_types, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Retrieve a specific assessment type by its primary key (id).
        """
        try:
            assessment_type = AssessmentType.objects.get(pk=pk)
            serializer = AssessmentTypeSerializer(assessment_type)
            return Response(serializer.data)
        except AssessmentType.DoesNotExist:
            return Response(
                {"detail": "Assessment type not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def create(self, request):
        """
        Create a new assessment type.
        """
        serializer = AssessmentTypeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {"detail": "Assessment type with this name already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """
        Update an existing assessment type.
        """
        try:
            assessment_type = AssessmentType.objects.get(pk=pk)
        except AssessmentType.DoesNotExist:
            return Response(
                {"detail": "Assessment type not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AssessmentTypeSerializer(assessment_type, data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data)
            except IntegrityError:
                return Response(
                    {"detail": "Assessment type with this name already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """Partially update an existing assessment type."""
        try:
            assessment_type = AssessmentType.objects.get(pk=pk)
        except AssessmentType.DoesNotExist:
            return Response(
                {"detail": "Assessment type not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AssessmentTypeSerializer(
            assessment_type, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        try:
            serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "Assessment type with this name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        """
        Delete an existing assessment type.
        """
        try:
            assessment_type = AssessmentType.objects.get(pk=pk)
            assessment_type.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AssessmentType.DoesNotExist:
            return Response(
                {"detail": "Assessment type not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
