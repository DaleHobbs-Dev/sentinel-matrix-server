"""Tests for Student API Methods"""

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
from sentinelapi.views.student import StudentSerializer

User = get_user_model()


class StudentComputedFieldTests(TestCase):
    """Test cases for verifying computed fields and serialization of students."""

    def setUp(self):
        user = User.objects.create_user(
            email="professor@example.com",
            password="StrongPass1!",
            first_name="Test",
            last_name="Professor",
        )
        instructor = Instructor.objects.create(user=user)
        self.student = Student.objects.create(
            first_name="Ada",
            last_name="Lovelace",
            student_id="S1001",
            email="ada@example.com",
            enrollment_date="2026-07-06",
            prior_academic_standing=Student.AcademicStanding.EXCELLENT,
        )

        homework_type = AssessmentType.objects.create(name="Homework")
        attendance_type = AssessmentType.objects.create(name="Attendance")

        for index, course_name in enumerate(["Algebra", "Biology"], start=1):
            course = Course.objects.create(
                instructor=instructor,
                course_name=course_name,
                description=f"{course_name} course",
                term="Fall",
            )
            enrollment = Enrollment.objects.create(student=self.student, course=course)

            homework_config = CourseAssessmentType.objects.create(
                course=course,
                assessment_type=homework_type,
                weight=Decimal("70"),
                risk_score_weight=Decimal("70"),
            )
            attendance_config = CourseAssessmentType.objects.create(
                course=course,
                assessment_type=attendance_type,
                weight=Decimal("30"),
                risk_score_weight=Decimal("30"),
            )

            completed_homework = Assessment.objects.create(
                course_assessment_type=homework_config,
                title=f"{course_name} Completed Homework",
                max_score=Decimal("100"),
                due_date=timezone.now(),
            )
            missing_homework = Assessment.objects.create(
                course_assessment_type=homework_config,
                title=f"{course_name} Missing Homework",
                max_score=Decimal("100"),
                due_date=timezone.now(),
            )
            attendance = Assessment.objects.create(
                course_assessment_type=attendance_config,
                title=f"{course_name} Attendance",
                max_score=Decimal("100"),
                due_date=timezone.now(),
            )

            StudentAssessment.objects.create(
                enrollment=enrollment,
                assessment=completed_homework,
                score=Decimal(70 + (index * 10)),
                completed_date=timezone.now(),
            )
            StudentAssessment.objects.create(
                enrollment=enrollment,
                assessment=missing_homework,
                is_missing=True,
            )
            StudentAssessment.objects.create(
                enrollment=enrollment,
                assessment=attendance,
                score=Decimal(80 + (index * 5)),
                completed_date=timezone.now(),
            )

    def test_student_computed_fields_use_all_enrollments(self):
        """Test that the student's computed fields are correctly calculated based on all their enrollments."""
        self.assertEqual(self.student.grade_average, Decimal("85.00"))
        self.assertEqual(self.student.attendance_rate, Decimal("87.50"))
        self.assertEqual(self.student.missing_assignment_rate, Decimal("50.00"))
        self.assertEqual(self.student.assignment_completion_rate, Decimal("50.00"))
        self.assertEqual(self.student.risk_score, Decimal("80.25"))
        self.assertEqual(self.student.risk_band, "Low Risk")

    def test_student_serializer_presents_computed_fields(self):
        """Test that the student serializer correctly presents the computed fields."""
        data = StudentSerializer(self.student).data

        self.assertEqual(data["grade_average"], Decimal("85.00"))
        self.assertEqual(data["attendance_rate"], Decimal("87.50"))
        self.assertEqual(data["missing_assignment_rate"], Decimal("50.00"))
        self.assertEqual(data["assignment_completion_rate"], Decimal("50.00"))
        self.assertEqual(data["risk_score"], Decimal("80.25"))
        self.assertEqual(data["risk_band"], "Low Risk")
