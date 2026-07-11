"""Serializers for the Student Assessment model.

Serializers included in this module:
    AssessmentSerializer       -- Serializes Assessment model data.
    StudentAssessmentSerializer -- Serializes StudentAssessment model data.
"""

from rest_framework import serializers
from sentinelapi.models import StudentAssessment, Assessment


class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Assessment model"""

    assessment_type_name = serializers.CharField(
        source="course_assessment_type.assessment_type.name",
        read_only=True,
    )

    class Meta:
        model = Assessment
        fields = [
            "id",
            "title",
            "max_score",
            "assessment_type_name",
        ]
        read_only_fields = [
            "id",
        ]


class StudentAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for StudentAssessment model"""

    assessment = serializers.PrimaryKeyRelatedField(queryset=Assessment.objects.all())

    def to_representation(self, instance):
        """Return expanded assessment details while accepting a student-assessment on writes."""
        data = super().to_representation(instance)
        data["assessment"] = AssessmentSerializer(instance.assessment).data
        return data

    def validate(self, attrs):
        """Treat omitted scores on updates as missing submissions."""
        score_was_provided = "score" in self.initial_data

        if self.instance is not None and not score_was_provided:
            attrs["score"] = None
            attrs["completed_date"] = None
            attrs["is_missing"] = True

        return attrs

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
