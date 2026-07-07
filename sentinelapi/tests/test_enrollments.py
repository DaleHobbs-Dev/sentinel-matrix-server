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
from sentinelapi.views.enrollment import EnrollmentSerializer

User = get_user_model()


class EnrollmentComputedFieldTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            email="professor@example.com",
            password="StrongPass1!",
            first_name="Test",
            last_name="Professor",
        )
        instructor = Instructor.objects.create(user=user)
        self.course = Course.objects.create(
            instructor=instructor,
            course_name="Algebra",
            description="Intro algebra",
            term="Fall",
        )
        self.student = Student.objects.create(
            first_name="Ada",
            last_name="Lovelace",
            student_id="S1001",
            email="ada@example.com",
            enrollment_date="2026-07-06",
            prior_academic_standing=Student.AcademicStanding.AT_RISK,
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
        )

        homework_type = AssessmentType.objects.create(name="Homework")
        attendance_type = AssessmentType.objects.create(name="Attendance")
        homework_config = CourseAssessmentType.objects.create(
            course=self.course,
            assessment_type=homework_type,
            weight=Decimal("70"),
            risk_score_weight=Decimal("70"),
        )
        attendance_config = CourseAssessmentType.objects.create(
            course=self.course,
            assessment_type=attendance_type,
            weight=Decimal("30"),
            risk_score_weight=Decimal("30"),
        )

        completed_homework = Assessment.objects.create(
            course_assessment_type=homework_config,
            title="Completed Homework",
            max_score=Decimal("100"),
            due_date=timezone.now(),
        )
        missing_homework = Assessment.objects.create(
            course_assessment_type=homework_config,
            title="Missing Homework",
            max_score=Decimal("100"),
            due_date=timezone.now(),
        )
        attendance = Assessment.objects.create(
            course_assessment_type=attendance_config,
            title="Week 1 Attendance",
            max_score=Decimal("100"),
            due_date=timezone.now(),
        )

        StudentAssessment.objects.create(
            enrollment=self.enrollment,
            assessment=completed_homework,
            score=Decimal("80"),
            completed_date=timezone.now(),
        )
        StudentAssessment.objects.create(
            enrollment=self.enrollment,
            assessment=missing_homework,
            is_missing=True,
        )
        StudentAssessment.objects.create(
            enrollment=self.enrollment,
            assessment=attendance,
            score=Decimal("90"),
            completed_date=timezone.now(),
        )

    def test_enrollment_computed_fields_use_enrollment_assessments(self):
        self.assertEqual(self.enrollment.grade_average, Decimal("80.00"))
        self.assertEqual(self.enrollment.prior_academic_standing, "at risk")
        self.assertEqual(self.enrollment.missing_assignment_rate, Decimal("50.00"))
        self.assertEqual(self.enrollment.risk_score, Decimal("75.00"))

    def test_enrollment_serializer_presents_computed_fields(self):
        data = EnrollmentSerializer(self.enrollment).data

        self.assertEqual(data["grade_average"], Decimal("80.00"))
        self.assertEqual(data["prior_academic_standing"], "at risk")
        self.assertEqual(data["missing_assignment_rate"], Decimal("50.00"))
        self.assertEqual(data["risk_score"], Decimal("75.00"))
