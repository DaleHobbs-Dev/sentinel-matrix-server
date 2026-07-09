from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from sentinelapi.models import (
    AssessmentType,
    Course,
    CourseAssessmentType,
    Instructor,
)
from sentinelapi.views.assessment import AssessmentSerializer

User = get_user_model()


class AssessmentSerializerTests(TestCase):
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
            course_name="Algebra",
            description="Intro algebra",
            term="Fall",
        )
        self.assessment_type = AssessmentType.objects.create(name="Quiz")
        self.course_assessment_type = CourseAssessmentType.objects.create(
            course=self.course,
            assessment_type=self.assessment_type,
            weight=Decimal("70"),
            risk_score_weight=Decimal("40"),
        )
        self.request = APIRequestFactory().post("/assessments")
        self.request.user = self.user

    def test_create_accepts_course_and_assessment_type_ids(self):
        serializer = AssessmentSerializer(
            data={
                "title": "Unit 1 Quiz",
                "max_score": "100.00",
                "due_date": timezone.now().isoformat(),
                "course_id": self.course.id,
                "assessment_type_id": self.assessment_type.id,
            },
            context={"request": self.request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        assessment = serializer.save()

        self.assertEqual(
            assessment.course_assessment_type,
            self.course_assessment_type,
        )
        self.assertEqual(serializer.data["course_id"], self.course.id)
        self.assertEqual(
            serializer.data["assessment_type_id"],
            self.assessment_type.id,
        )
        self.assertEqual(serializer.data["assessment_type_name"], "Quiz")
        self.assertEqual(serializer.data["weight"], "70.00")
        self.assertEqual(serializer.data["risk_score_weight"], "40.00")
