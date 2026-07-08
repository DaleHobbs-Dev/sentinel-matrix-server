from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

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

User = get_user_model()


class CourseDashboardTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="professor@example.com",
            password="StrongPass1!",
            first_name="Test",
            last_name="Professor",
        )
        instructor = Instructor.objects.create(user=self.user)
        self.course = Course.objects.create(
            instructor=instructor,
            course_name="College Algebra",
            description="Foundational algebra course",
            term="Fall",
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
        self.completed_homework = Assessment.objects.create(
            course_assessment_type=homework_config,
            title="Completed Homework",
            max_score=Decimal("100"),
            due_date=timezone.now(),
        )
        self.missing_homework = Assessment.objects.create(
            course_assessment_type=homework_config,
            title="Missing Homework",
            max_score=Decimal("100"),
            due_date=timezone.now(),
        )
        self.attendance = Assessment.objects.create(
            course_assessment_type=attendance_config,
            title="Attendance",
            max_score=Decimal("100"),
            due_date=timezone.now(),
        )

        self._create_enrollment(
            first_name="Ava",
            last_name="Nguyen",
            student_id="A00000005",
            email="ava@example.com",
            prior_academic_standing=Student.AcademicStanding.GOOD,
            homework_score=Decimal("80"),
            attendance_score=Decimal("90"),
            homework_missing=True,
        )
        self._create_enrollment(
            first_name="Ben",
            last_name="Ortiz",
            student_id="A00000006",
            email="ben@example.com",
            prior_academic_standing=Student.AcademicStanding.AT_RISK,
            homework_score=Decimal("50"),
            attendance_score=Decimal("50"),
            homework_missing=True,
        )
        self._create_enrollment(
            first_name="Cara",
            last_name="Patel",
            student_id="A00000007",
            email="cara@example.com",
            prior_academic_standing=Student.AcademicStanding.AT_RISK,
            homework_score=Decimal("20"),
            attendance_score=Decimal("30"),
            homework_missing=True,
        )

    def _create_enrollment(
        self,
        *,
        first_name,
        last_name,
        student_id,
        email,
        prior_academic_standing,
        homework_score,
        attendance_score,
        homework_missing,
    ):
        student = Student.objects.create(
            first_name=first_name,
            last_name=last_name,
            student_id=student_id,
            email=email,
            enrollment_date="2026-07-06",
            prior_academic_standing=prior_academic_standing,
        )
        enrollment = Enrollment.objects.create(student=student, course=self.course)
        StudentAssessment.objects.create(
            enrollment=enrollment,
            assessment=self.completed_homework,
            score=homework_score,
            completed_date=timezone.now(),
        )
        StudentAssessment.objects.create(
            enrollment=enrollment,
            assessment=self.missing_homework,
            is_missing=homework_missing,
        )
        StudentAssessment.objects.create(
            enrollment=enrollment,
            assessment=self.attendance,
            score=attendance_score,
            completed_date=timezone.now(),
        )
        return enrollment

    def test_dashboard_returns_course_metrics_and_students(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(f"/courses/{self.course.id}/dashboard")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.course.id)
        self.assertEqual(response.data["course_name"], "College Algebra")
        self.assertEqual(response.data["description"], "Foundational algebra course")
        self.assertEqual(
            response.data["metrics"],
            {
                "average_grade": 50.0,
                "attendance_rate": 56.67,
                "high_risk_student_count": 1,
                "moderate_risk_student_count": 1,
            },
        )
        self.assertEqual(len(response.data["students"]), 3)
        self.assertEqual(
            response.data["students"][0],
            {
                "id": Student.objects.get(student_id="A00000005").id,
                "student_id": "A00000005",
                "first_name": "Ava",
                "last_name": "Nguyen",
                "grade_average": 80.0,
                "attendance_rate": 90.0,
                "missing_assignment_count": 1,
                "risk_band": "Low Risk",
            },
        )

    def test_dashboard_requires_authentication(self):
        response = self.client.get(f"/courses/{self.course.id}/dashboard")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
