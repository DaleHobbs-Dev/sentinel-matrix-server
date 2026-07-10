from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory

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


class AssessmentStudentAssessmentActionTests(APITestCase):
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
        self.assessment_type = AssessmentType.objects.create(name="Homework")
        self.course_assessment_type = CourseAssessmentType.objects.create(
            course=self.course,
            assessment_type=self.assessment_type,
            weight=Decimal("70"),
            risk_score_weight=Decimal("40"),
        )
        self.assessment = Assessment.objects.create(
            course_assessment_type=self.course_assessment_type,
            title="Homework 1",
            max_score=Decimal("100"),
            due_date=timezone.now(),
        )
        self.students = [
            Student.objects.create(
                first_name="Ada",
                last_name="Lovelace",
                student_id="S1001",
                email="ada@example.com",
                enrollment_date="2026-07-06",
                prior_academic_standing=Student.AcademicStanding.EXCELLENT,
            ),
            Student.objects.create(
                first_name="Grace",
                last_name="Hopper",
                student_id="S1002",
                email="grace@example.com",
                enrollment_date="2026-07-06",
                prior_academic_standing=Student.AcademicStanding.GREAT,
            ),
        ]
        self.student_assessments = []
        for student in self.students:
            enrollment = Enrollment.objects.create(
                student=student,
                course=self.course,
            )
            self.student_assessments.append(
                StudentAssessment.objects.create(
                    enrollment=enrollment,
                    assessment=self.assessment,
                    is_missing=True,
                )
            )

    def test_student_assessments_action_lists_rows_for_assessment(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f"/assessments/{self.assessment.id}/student-assessments"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            {row["id"] for row in response.data},
            {
                student_assessment.id
                for student_assessment in self.student_assessments
            },
        )

    def test_student_assessments_action_bulk_updates_scores_and_missing_status(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f"/assessments/{self.assessment.id}/student-assessments",
            {
                "student_assessments": [
                    {
                        "id": self.student_assessments[0].id,
                        "score": "92.00",
                    },
                    {
                        "id": self.student_assessments[1].id,
                        "is_missing": True,
                    },
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_assessments[0].refresh_from_db()
        self.student_assessments[1].refresh_from_db()
        self.assertEqual(self.student_assessments[0].score, Decimal("92.00"))
        self.assertIsNotNone(self.student_assessments[0].completed_date)
        self.assertFalse(self.student_assessments[0].is_missing)
        self.assertIsNone(self.student_assessments[1].score)
        self.assertIsNone(self.student_assessments[1].completed_date)
        self.assertTrue(self.student_assessments[1].is_missing)

    def test_student_assessments_action_rejects_rows_for_other_assessments(self):
        other_assessment = Assessment.objects.create(
            course_assessment_type=self.course_assessment_type,
            title="Homework 2",
            max_score=Decimal("100"),
            due_date=timezone.now(),
        )
        other_student_assessment = StudentAssessment.objects.create(
            enrollment=self.student_assessments[0].enrollment,
            assessment=other_assessment,
            is_missing=True,
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f"/assessments/{self.assessment.id}/student-assessments",
            {
                "student_assessments": [
                    {
                        "id": self.student_assessments[0].id,
                        "score": "92.00",
                    },
                    {
                        "id": other_student_assessment.id,
                        "score": "88.00",
                    },
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.student_assessments[0].refresh_from_db()
        other_student_assessment.refresh_from_db()
        self.assertIsNone(self.student_assessments[0].score)
        self.assertIsNone(other_student_assessment.score)
