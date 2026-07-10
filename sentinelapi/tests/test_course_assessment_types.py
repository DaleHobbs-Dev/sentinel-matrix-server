from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from sentinelapi.models import (
    AssessmentType,
    Course,
    CourseAssessmentType,
    Instructor,
)

User = get_user_model()


class CourseAssessmentTypeViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="professor@example.com",
            password="StrongPass1!",
            first_name="Test",
            last_name="Professor",
        )
        self.instructor = Instructor.objects.create(user=self.user)
        self.course = Course.objects.create(
            instructor=self.instructor,
            course_name="College Algebra",
            description="Foundational algebra course",
            term="Fall",
        )
        self.homework_type = AssessmentType.objects.create(name="Homework")
        self.attendance_type = AssessmentType.objects.create(name="Attendance")
        self.homework_config = CourseAssessmentType.objects.create(
            course=self.course,
            assessment_type=self.homework_type,
            weight=Decimal("80"),
            risk_score_weight=Decimal("40"),
        )

    def test_list_filters_to_authenticated_instructor_courses(self):
        other_user = User.objects.create_user(
            email="other@example.com",
            password="StrongPass1!",
            first_name="Other",
            last_name="Professor",
        )
        other_instructor = Instructor.objects.create(user=other_user)
        other_course = Course.objects.create(
            instructor=other_instructor,
            course_name="Biology",
            description="Biology course",
            term="Fall",
        )
        CourseAssessmentType.objects.create(
            course=other_course,
            assessment_type=self.attendance_type,
            weight=Decimal("20"),
            risk_score_weight=Decimal("60"),
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/course-assessment-types")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.homework_config.id)
        self.assertEqual(response.data[0]["assessment_type_name"], "Homework")

    def test_create_course_assessment_type_for_owned_course(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/course-assessment-types",
            {
                "course": self.course.id,
                "assessment_type": self.attendance_type.id,
                "weight": "20.00",
                "risk_score_weight": "60.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["course"], self.course.id)
        self.assertEqual(response.data["assessment_type"], self.attendance_type.id)
        self.assertEqual(response.data["assessment_type_name"], "Attendance")
        self.assertEqual(response.data["risk_score_weight"], "30.00")

    def test_patch_updates_weight_but_keeps_risk_score_weight_fixed(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f"/course-assessment-types/{self.homework_config.id}",
            {
                "weight": "75.00",
                "risk_score_weight": "45.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.homework_config.refresh_from_db()
        self.assertEqual(self.homework_config.weight, Decimal("75.00"))
        self.assertEqual(
            self.homework_config.risk_score_weight,
            Decimal("40.00"),
        )
        self.assertEqual(response.data["risk_score_weight"], "40.00")

    def test_model_sets_fixed_risk_score_weight(self):
        config = CourseAssessmentType.objects.create(
            course=self.course,
            assessment_type=self.attendance_type,
            weight=Decimal("20"),
            risk_score_weight=Decimal("99"),
        )

        self.assertEqual(config.risk_score_weight, Decimal("30.00"))
