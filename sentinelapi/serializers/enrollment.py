"""Serializers for Enrollment Related Models"""

from rest_framework import serializers
from sentinelapi.models import Enrollment, Student
from sentinelapi.serializers.student import StudentSummarySerializer


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for Enrollment model"""

    grade_average = serializers.ReadOnlyField()
    attendance_rate = serializers.ReadOnlyField()
    prior_academic_standing = serializers.ReadOnlyField()
    missing_assignment_rate = serializers.ReadOnlyField()
    risk_score = serializers.ReadOnlyField()
    risk_band = serializers.ReadOnlyField()
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())

    def to_representation(self, instance):
        """Return expanded student details while accepting a student id on writes."""
        data = super().to_representation(instance)
        data["student"] = StudentSummarySerializer(instance.student).data
        return data

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "course",
            "enrolled_at",
            "grade_average",
            "attendance_rate",
            "prior_academic_standing",
            "missing_assignment_rate",
            "risk_score",
            "risk_band",
            "student",
        ]
        read_only_fields = [
            "id",
            "enrolled_at",
            "grade_average",
            "attendance_rate",
            "prior_academic_standing",
            "missing_assignment_rate",
            "risk_score",
            "risk_band",
        ]
