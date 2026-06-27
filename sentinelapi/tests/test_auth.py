from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from sentinelapi.models import Instructor

User = get_user_model()


class AuthTests(APITestCase):
    def test_register_creates_instructor_and_returns_token(self):
        response = self.client.post(
            "/register",
            {
                "password": "StrongPass1!",
                "email": "grace@example.com",
                "first_name": "Grace",
                "last_name": "Hopper",
                "subject_taught": "Computer Science",
                "university": "Example University",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["email"], "grace@example.com")

        user = User.objects.get(email="grace@example.com")
        self.assertTrue(user.check_password("StrongPass1!"))
        self.assertTrue(Token.objects.filter(user=user).exists())
        self.assertTrue(
            Instructor.objects.filter(
                user=user,
                subject_taught="Computer Science",
                university="Example University",
            ).exists()
        )

    def test_register_validates_password_strength(self):
        response = self.client.post(
            "/register",
            {
                "password": "password",
                "email": "ada@example.com",
                "first_name": "Ada",
                "last_name": "Lovelace",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(email="ada@example.com").exists())
        self.assertEqual(Instructor.objects.count(), 0)

    def test_register_rejects_email_with_different_casing(self):
        User.objects.create_user(email="Grace@Example.com", password="StrongPass1!")

        response = self.client.post(
            "/register",
            {
                "password": "AnotherStrong2!",
                "email": "grace@example.com",
                "first_name": "Grace",
                "last_name": "Hopper",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(User.objects.filter(email__iexact="grace@example.com").count(), 1)

    def test_login_returns_existing_token(self):
        user = User.objects.create_user(
            password="StrongPass1!",
            email="alan@example.com",
            first_name="Alan",
            last_name="Turing",
        )

        response = self.client.post(
            "/login",
            {"email": "alan@example.com", "password": "StrongPass1!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], user.email)
        self.assertEqual(response.data["token"], Token.objects.get(user=user).key)

    def test_login_email_is_case_insensitive(self):
        user = User.objects.create_user(
            email="Katherine@Example.com",
            password="StrongPass1!",
        )

        response = self.client.post(
            "/login",
            {"email": "kAtHeRiNe@example.COM", "password": "StrongPass1!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], user.email)

    def test_login_rejects_invalid_credentials(self):
        User.objects.create_user(
            email="katherine@example.com", password="StrongPass1!"
        )

        response = self.client.post(
            "/login",
            {"email": "katherine@example.com", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", response.data)
