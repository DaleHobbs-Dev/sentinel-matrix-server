"""Views for handling assessment-related API requests."""

from django.db import IntegrityError
from django.db.models import Q
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.response import Response

from sentinelapi.models import Assessment, CourseAssessmentType


class AssessmentSerializer(serializers.ModelSerializer):
    """Serialize an assessment with its course-specific type details."""

    course_id = serializers.IntegerField(required=False, write_only=True)
    assessment_type_id = serializers.IntegerField(required=False, write_only=True)
    course_assessment_type_id = serializers.IntegerField(
        source="course_assessment_type.id",
        read_only=True,
    )
    assessment_type_name = serializers.CharField(
        source="course_assessment_type.assessment_type.name",
        read_only=True,
    )
    weight = serializers.DecimalField(
        source="course_assessment_type.weight",
        max_digits=5,
        decimal_places=2,
        read_only=True,
    )
    risk_score_weight = serializers.DecimalField(
        source="course_assessment_type.risk_score_weight",
        max_digits=5,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Assessment
        fields = [
            "id",
            "title",
            "max_score",
            "due_date",
            "course_id",
            "course_assessment_type_id",
            "assessment_type_id",
            "assessment_type_name",
            "weight",
            "risk_score_weight",
        ]
        read_only_fields = ["id"]

    def to_representation(self, instance):
        """Return course/type fields flattened for client filtering and display."""
        data = super().to_representation(instance)
        data["course_id"] = instance.course_assessment_type.course_id
        data["assessment_type_id"] = instance.course_assessment_type.assessment_type_id
        return data

    def validate(self, attrs):
        """Resolve course/type input to the course's assessment type config."""
        course_id = attrs.pop("course_id", None)
        assessment_type_id = attrs.pop("assessment_type_id", None)

        if self.instance is None and (course_id is None or assessment_type_id is None):
            raise serializers.ValidationError(
                {
                    "course_id": "This field is required.",
                    "assessment_type_id": "This field is required.",
                }
            )

        if course_id is None and assessment_type_id is None:
            return attrs

        if course_id is None or assessment_type_id is None:
            raise serializers.ValidationError(
                "Both course_id and assessment_type_id are required together."
            )

        request = self.context.get("request")
        filters = {
            "course_id": course_id,
            "assessment_type_id": assessment_type_id,
        }

        if request:
            filters["course__instructor__user"] = request.user

        try:
            attrs["course_assessment_type"] = CourseAssessmentType.objects.get(
                **filters
            )
        except CourseAssessmentType.DoesNotExist as exc:
            raise serializers.ValidationError(
                (
                    "Course assessment type configuration not found for "
                    "this course and assessment type."
                )
            ) from exc

        return attrs

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
