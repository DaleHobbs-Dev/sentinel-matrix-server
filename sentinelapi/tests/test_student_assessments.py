from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from sentinelapi.models import (
    Assessment,
    AssessmentType,
    Course,
    CourseAssessmentType,
    Enrollment,
    Instructor,
    Student,
    StudentAssessment,
)
from sentinelapi.views.student_assessment import StudentAssessmentSerializer

User = get_user_model()


class StudentAssessmentMissingStateTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            email="professor@example.com",
            password="StrongPass1!",
            first_name="Test",
            last_name="Professor",
        )
        instructor = Instructor.objects.create(user=user)
        course = Course.objects.create(
            instructor=instructor,
            course_name="Algebra",
            description="Intro algebra",
            term="Fall",
        )
        student = Student.objects.create(
            first_name="Ada",
            last_name="Lovelace",
            student_id="S1001",
            email="ada@example.com",
            enrollment_date="2026-07-06",
            prior_academic_standing=Student.AcademicStanding.GOOD,
        )
        self.enrollment = Enrollment.objects.create(student=student, course=course)

        assessment_type = AssessmentType.objects.create(name="Homework")
        course_assessment_type = CourseAssessmentType.objects.create(
            course=course,
            assessment_type=assessment_type,
            weight=Decimal("70"),
            risk_score_weight=Decimal("70"),
        )
        self.assessment = Assessment.objects.create(
            course_assessment_type=course_assessment_type,
            title="Homework 1",
            max_score=Decimal("100"),
            due_date=timezone.now(),
        )

    def test_model_marks_unscored_assessment_missing(self):
        student_assessment = StudentAssessment.objects.create(
            enrollment=self.enrollment,
            assessment=self.assessment,
            is_missing=False,
        )

        self.assertTrue(student_assessment.is_missing)

    def test_model_clears_missing_when_score_is_saved(self):
        student_assessment = StudentAssessment.objects.create(
            enrollment=self.enrollment,
            assessment=self.assessment,
            is_missing=True,
        )

        student_assessment.score = Decimal("85")
        student_assessment.completed_date = timezone.now()
        student_assessment.is_missing = True
        student_assessment.save()
        student_assessment.refresh_from_db()

        self.assertFalse(student_assessment.is_missing)

    def test_serializer_create_without_score_marks_assessment_missing(self):
        serializer = StudentAssessmentSerializer(
            data={
                "enrollment": self.enrollment.id,
                "assessment": self.assessment.id,
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        student_assessment = serializer.save()

        self.assertTrue(student_assessment.is_missing)

    def test_serializer_update_with_score_clears_missing(self):
        student_assessment = StudentAssessment.objects.create(
            enrollment=self.enrollment,
            assessment=self.assessment,
            is_missing=True,
        )
        completed_date = timezone.now()
        serializer = StudentAssessmentSerializer(
            student_assessment,
            data={
                "score": "85.00",
                "completed_date": completed_date.isoformat(),
                "is_missing": True,
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertFalse(updated.is_missing)

    def test_serializer_full_update_without_score_marks_missing(self):
        student_assessment = StudentAssessment.objects.create(
            enrollment=self.enrollment,
            assessment=self.assessment,
            score=Decimal("85"),
            completed_date=timezone.now(),
        )
        serializer = StudentAssessmentSerializer(
            student_assessment,
            data={
                "enrollment": self.enrollment.id,
                "assessment": self.assessment.id,
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertIsNone(updated.score)
        self.assertIsNone(updated.completed_date)
        self.assertTrue(updated.is_missing)

    def test_serializer_partial_update_without_score_marks_missing(self):
        student_assessment = StudentAssessment.objects.create(
            enrollment=self.enrollment,
            assessment=self.assessment,
            score=Decimal("85"),
            completed_date=timezone.now(),
        )
        serializer = StudentAssessmentSerializer(
            student_assessment,
            data={"is_missing": True},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertIsNone(updated.score)
        self.assertIsNone(updated.completed_date)
        self.assertTrue(updated.is_missing)
