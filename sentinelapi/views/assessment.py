"""Views for handling assessment-related API requests."""

from django.db import IntegrityError
from django.db.models import Q
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.response import Response

from sentinelapi.models import Assessment, CourseAssessmentType
from .assessment_type import AssessmentTypeSerializer


class CourseAssessmentTypeSerializer(serializers.ModelSerializer):
    """Display a course's assessment type and its configured weights."""

    assessment_type = AssessmentTypeSerializer(read_only=True)

    class Meta:
        model = CourseAssessmentType
        fields = [
            "id",
            "course",
            "assessment_type",
            "weight",
            "risk_score_weight",
        ]


class AssessmentSerializer(serializers.ModelSerializer):
    """Serialize an assessment with its course-specific type details."""

    course_assessment_type = CourseAssessmentTypeSerializer(read_only=True)
    course_assessment_type_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Assessment
        fields = [
            "id",
            "title",
            "max_score",
            "due_date",
            "course_assessment_type",
            "course_assessment_type_id",
        ]
        read_only_fields = ["id"]

    def validate_course_assessment_type_id(self, value):
        """Require a valid configuration owned by the requesting instructor."""
        try:
            course_assessment_type = CourseAssessmentType.objects.get(pk=value)
        except CourseAssessmentType.DoesNotExist as exc:
            raise serializers.ValidationError(
                "Course assessment type not found."
            ) from exc

        request = self.context.get("request")
        if request and course_assessment_type.course.instructor.user != request.user:
            raise serializers.ValidationError(
                "You may only create assessments for your own courses."
            )

        return value

    def validate_max_score(self, value):
        """Assessment maximum scores must be greater than zero."""
        if value <= 0:
            raise serializers.ValidationError("Max score must be greater than zero.")
        return value


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

        assessments = Assessment.objects.filter(filters)
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
