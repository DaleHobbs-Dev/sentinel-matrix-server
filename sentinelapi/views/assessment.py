"""Views for handling assessment-related API requests."""

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from sentinelapi.models import Assessment, Enrollment, StudentAssessment
from sentinelapi.serializers import AssessmentSerializer
from sentinelapi.views.student_assessment import StudentAssessmentSerializer


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

    @action(detail=True, methods=["get", "patch"], url_path="student-assessments")
    def student_assessments(self, request, pk=None):
        """Retrieve or partially update student assessments for a specific assessment."""
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

        student_assessments = StudentAssessment.objects.filter(
            assessment=assessment,
        ).select_related("enrollment", "assessment")

        if request.method == "GET":
            serializer = StudentAssessmentSerializer(
                student_assessments,
                context={"request": request},
                many=True,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == "PATCH":
            updates = request.data.get("student_assessments")
            if not isinstance(updates, list):
                return Response(
                    {"detail": "student_assessments must be a list."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializers_to_save = []
            for index, student_assessment in enumerate(updates):
                if not isinstance(student_assessment, dict):
                    return Response(
                        {
                            "detail": (
                                f"student_assessments[{index}] must be an object."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                data = student_assessment.copy()
                data["assessment"] = assessment.id

                student_assessment_id = student_assessment.get("id")
                enrollment_id = student_assessment.get("enrollment")

                if student_assessment_id is not None:
                    try:
                        student_assessment_instance = student_assessments.get(
                            pk=student_assessment_id
                        )
                    except StudentAssessment.DoesNotExist:
                        return Response(
                            {
                                "detail": (
                                    "Student assessment not found for this assessment."
                                )
                            },
                            status=status.HTTP_404_NOT_FOUND,
                        )
                    if (
                        enrollment_id is not None
                        and str(enrollment_id)
                        != str(student_assessment_instance.enrollment_id)
                    ):
                        return Response(
                            {
                                "detail": (
                                    f"student_assessments[{index}].enrollment does "
                                    "not match the student assessment."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    data["enrollment"] = student_assessment_instance.enrollment_id
                else:
                    if enrollment_id is None:
                        return Response(
                            {
                                "detail": (
                                    f"student_assessments[{index}].id or "
                                    "enrollment is required."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    try:
                        enrollment = Enrollment.objects.get(
                            pk=enrollment_id,
                            course=assessment.course_assessment_type.course,
                        )
                    except Enrollment.DoesNotExist:
                        return Response(
                            {
                                "detail": (
                                    "Enrollment not found for this assessment's course."
                                )
                            },
                            status=status.HTTP_404_NOT_FOUND,
                        )

                    student_assessment_instance = student_assessments.filter(
                        enrollment=enrollment
                    ).first()
                    data["enrollment"] = enrollment.id

                if data.get("is_missing") is True:
                    data["score"] = None
                    data["completed_date"] = None
                elif data.get("score") is not None and "score" in data:
                    data.setdefault(
                        "completed_date",
                        timezone.now().isoformat(),
                    )

                if student_assessment_instance is None:
                    serializer = StudentAssessmentSerializer(
                        data=data,
                        context={"request": request},
                    )
                else:
                    serializer = StudentAssessmentSerializer(
                        student_assessment_instance,
                        data=data,
                        partial=True,
                        context={"request": request},
                    )
                serializer.is_valid(raise_exception=True)
                serializers_to_save.append(serializer)

            try:
                with transaction.atomic():
                    for serializer in serializers_to_save:
                        serializer.save()
            except IntegrityError:
                return Response(
                    {"detail": "Unable to update student assessments."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = StudentAssessmentSerializer(
                student_assessments,
                context={"request": request},
                many=True,
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
