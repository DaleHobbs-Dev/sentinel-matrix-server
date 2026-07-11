"""Serializers for Assessment Related Models"""

from rest_framework import serializers
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
        # super() extends the built-in serialized representation of the
        # instance with additional course/type fields.
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
