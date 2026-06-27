"""Custom user model for email-based authentication."""

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    """Create users whose email address is their login identifier."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Build and save a user after normalizing their email address."""
        if not email:
            raise ValueError("Users must have an email address.")

        # Django's normalize_email only lowercases the domain. We lowercase the
        # whole address so login and uniqueness behave consistently for users.
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Never store a raw password in the database.
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create a regular, non-staff user."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create an administrator while enforcing Django's required flags."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Application user authenticated by email instead of username.

    AbstractUser still gives us Django's password, permissions, name, staff,
    and active-account fields. Setting ``username`` to ``None`` removes only
    the field we no longer want.
    """

    username = None
    email = models.EmailField("email address", unique=True)

    # Django's authentication system reads these settings from the model.
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # Email and password are already prompted separately.

    objects = UserManager()

    def save(self, *args, **kwargs):
        """Keep stored emails normalized even outside UserManager."""
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email).lower()
        super().save(*args, **kwargs)

    def __str__(self):
        """Use the login identifier in admin pages and logs."""
        return self.email
