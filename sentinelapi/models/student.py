"""Model for Students"""

from django.db import models


# Blueprint for the Student objects
# Student class inherits from Django's models.Model base class
# This provides built-in functionality for database operations.
class Student(models.Model):
    """Model for Students"""

    # Create instances of models.XXXField classes to define the fields of the Student model.
    # Each field corresponds to a column in the database table.
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    enrollment_date = models.DateField()

    # Academic Standing class with choices for "Good" and "At Risk"
    class AcademicStanding(models.TextChoices):
        """Choices for Academic Standing of Students"""

        GOOD = "good", "Good"
        AT_RISK = "at risk", "At Risk"

    prior_academic_standing = models.CharField(
        max_length=100,
        choices=AcademicStanding.choices,
        default=AcademicStanding.GOOD,
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    # Meta class for additional model options
    class Meta:
        """
        Ensure that the prior_academic_standing field
        can only have values of 'good' or 'at risk'
        """

        constraints = [
            models.CheckConstraint(
                condition=models.Q(prior_academic_standing__in=["good", "at risk"]),
                name="valid_prior_academic_standing",
            ),
        ]
