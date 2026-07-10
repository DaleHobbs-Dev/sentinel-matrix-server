"""Test for Courses API Methods"""

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
    """Tests for the course dashboard API."""

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
            prior_academic_standing=Student.AcademicStanding.EXCELLENT,
            homework_score=Decimal("80"),
            attendance_score=Decimal("90"),
            homework_missing=True,
        )
        self._create_enrollment(
            first_name="Cara",
            last_name="Patel",
            student_id="A00000007",
            email="cara@example.com",
            prior_academic_standing=Student.AcademicStanding.GREAT,
            homework_score=Decimal("20"),
            attendance_score=Decimal("30"),
            homework_missing=True,
        )
        self._create_enrollment(
            first_name="Dana",
            last_name="Lee",
            student_id="A00000008",
            email="dana@example.com",
            prior_academic_standing=Student.AcademicStanding.AVERAGE,
            homework_score=Decimal("60"),
            attendance_score=Decimal("70"),
            homework_missing=False,
        )
        self._create_enrollment(
            first_name="Ben",
            last_name="Ortiz",
            student_id="A00000006",
            email="ben@example.com",
            prior_academic_standing=Student.AcademicStanding.POOR,
            homework_score=Decimal("50"),
            attendance_score=Decimal("50"),
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
        """Test that the course dashboard returns the correct metrics and student list."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(f"/courses/{self.course.id}/dashboard")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.course.id)
        self.assertEqual(response.data["course_name"], "College Algebra")
        self.assertEqual(response.data["description"], "Foundational algebra course")
        self.assertEqual(
            response.data["metrics"],
            {
                "average_grade": 52.5,
                "attendance_rate": 60.0,
                "high_risk_student_count": 1,
                "moderate_risk_student_count": 2,
            },
        )
        self.assertEqual(len(response.data["students"]), 4)
        self.assertEqual(
            response.data["students"][0],
            {
                "id": Student.objects.get(student_id="A00000008").id,
                "student_id": "A00000008",
                "first_name": "Dana",
                "last_name": "Lee",
                "grade_average": 60.0,
                "attendance_rate": 70.0,
                "missing_assignment_count": 1,
                "risk_band": "Moderate Risk",
            },
        )

    def test_dashboard_requires_authentication(self):
        """Test that accessing the course dashboard without authentication is forbidden."""
        response = self.client.get(f"/courses/{self.course.id}/dashboard")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_instructor_dashboard_returns_summary_and_risk_students(self):
        """Test that the instructor dashboard returns the correct summary and list of at-risk students."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/courses/dashboard")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_course_count"], 1)
        self.assertEqual(response.data["total_student_count"], 4)
        self.assertEqual(response.data["high_risk_student_count"], 1)
        self.assertEqual(response.data["moderate_risk_student_count"], 2)
        self.assertEqual(
            response.data["risk_students"],
            [
                {
                    "student_id": "A00000007",
                    "course_id": self.course.id,
                    "full_name": "Cara Patel",
                    "course": "College Algebra",
                    "risk_score": 35.5,
                    "risk_band": "High Risk",
                },
                {
                    "student_id": "A00000008",
                    "course_id": self.course.id,
                    "full_name": "Dana Lee",
                    "course": "College Algebra",
                    "risk_score": 62.0,
                    "risk_band": "Moderate Risk",
                },
                {
                    "student_id": "A00000006",
                    "course_id": self.course.id,
                    "full_name": "Ben Ortiz",
                    "course": "College Algebra",
                    "risk_score": 50.0,
                    "risk_band": "Moderate Risk",
                },
            ],
        )

    def test_instructor_dashboard_excludes_other_instructors_courses(self):
        """Test that the instructor dashboard does not include courses from other instructors."""
        other_user = User.objects.create_user(
            email="other@example.com",
            password="StrongPass1!",
            first_name="Other",
            last_name="Professor",
        )
        other_instructor = Instructor.objects.create(user=other_user)
        Course.objects.create(
            instructor=other_instructor,
            course_name="Biology",
            description="Other instructor course",
            term="Fall",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/courses/dashboard")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_course_count"], 1)

    def test_instructor_dashboard_requires_instructor_profile(self):
        """Test that accessing the instructor dashboard without an instructor profile is forbidden."""
        student_user = User.objects.create_user(
            email="student-user@example.com",
            password="StrongPass1!",
            first_name="Student",
            last_name="User",
        )
        self.client.force_authenticate(user=student_user)

        response = self.client.get("/courses/dashboard")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CourseCreateTests(APITestCase):
    """Test cases for creating courses and ensuring default assessment type configurations are applied correctly."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="professor@example.com",
            password="StrongPass1!",
            first_name="Test",
            last_name="Professor",
        )
        Instructor.objects.create(user=self.user)
        AssessmentType.objects.create(name="Attendance")
        AssessmentType.objects.create(name="Homework")

    def test_create_course_creates_default_assessment_type_configs(self):
        """Test that creating a course automatically creates default assessment type configurations."""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/courses",
            {
                "course_name": "College Algebra",
                "description": "Foundational algebra course",
                "term": "Fall",
                "course_image_url": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        course = Course.objects.get(pk=response.data["id"])
        configs = {
            config.assessment_type.name: config
            for config in CourseAssessmentType.objects.filter(course=course)
        }

        self.assertEqual(set(configs), {"Attendance", "Homework"})
        self.assertEqual(configs["Attendance"].weight, Decimal("20.00"))
        self.assertEqual(
            configs["Attendance"].risk_score_weight,
            Decimal("30.00"),
        )
        self.assertEqual(configs["Homework"].weight, Decimal("80.00"))
        self.assertEqual(
            configs["Homework"].risk_score_weight,
            Decimal("40.00"),
        )
