"""Views for handling course-specific assessment type configuration."""

from django.db import IntegrityError
from django.db.models import Q
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.response import Response

from sentinelapi.models import CourseAssessmentType


class CourseAssessmentTypeSerializer(serializers.ModelSerializer):
    """Serialize assessment type weights configured for a course."""

    assessment_type_name = serializers.CharField(
        source="assessment_type.name",
        read_only=True,
    )

    class Meta:
        model = CourseAssessmentType
        fields = [
            "id",
            "course",
            "assessment_type",
            "assessment_type_name",
            "weight",
            "risk_score_weight",
        ]
        read_only_fields = ["id", "assessment_type_name", "risk_score_weight"]

    def validate_course(self, value):
        """Only allow instructors to configure their own courses."""
        request = self.context.get("request")
        if request and value.instructor.user != request.user:
            raise serializers.ValidationError(
                "You may only configure assessment types for your own courses."
            )
        return value


class CourseAssessmentTypeViewSet(viewsets.ViewSet):
    """Manage course-specific assessment type weights."""

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """List course assessment type configurations for the instructor."""
        course_id = request.query_params.get("course_id")
        assessment_type_id = request.query_params.get("assessment_type_id")

        filters = Q(course__instructor__user=request.user)
        if course_id:
            filters &= Q(course_id=course_id)
        if assessment_type_id:
            filters &= Q(assessment_type_id=assessment_type_id)

        course_assessment_types = CourseAssessmentType.objects.filter(
            filters
        ).select_related("course", "assessment_type")
        serializer = CourseAssessmentTypeSerializer(
            course_assessment_types,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Retrieve one course assessment type configuration."""
        try:
            course_assessment_type = CourseAssessmentType.objects.select_related(
                "course",
                "assessment_type",
            ).get(pk=pk, course__instructor__user=request.user)
        except CourseAssessmentType.DoesNotExist:
            return Response(
                {"detail": "Course assessment type not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CourseAssessmentTypeSerializer(
            course_assessment_type,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """Create a course assessment type configuration."""
        serializer = CourseAssessmentTypeSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        try:
            serializer.save()
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "This assessment type is already configured for "
                        "the selected course."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        """Replace a course assessment type configuration."""
        return self._update(request, pk, partial=False)

    def partial_update(self, request, pk=None):
        """Partially update a course assessment type configuration."""
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        try:
            course_assessment_type = CourseAssessmentType.objects.get(
                pk=pk,
                course__instructor__user=request.user,
            )
        except CourseAssessmentType.DoesNotExist:
            return Response(
                {"detail": "Course assessment type not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CourseAssessmentTypeSerializer(
            course_assessment_type,
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
                        "This assessment type is already configured for "
                        "the selected course."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.data, status=status.HTTP_200_OK)
