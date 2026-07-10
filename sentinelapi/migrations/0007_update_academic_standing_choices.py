"""Update student academic standing choices."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sentinelapi", "0006_assessment_studentassessment_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="student",
            name="valid_prior_academic_standing",
        ),
        migrations.AlterField(
            model_name="student",
            name="prior_academic_standing",
            field=models.CharField(
                choices=[
                    ("excellent", "Excellent"),
                    ("great", "Great"),
                    ("average", "Average"),
                    ("poor", "Poor"),
                ],
                default="excellent",
                max_length=100,
            ),
        ),
        migrations.AddConstraint(
            model_name="student",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("prior_academic_standing__in", [
                        "excellent",
                        "great",
                        "average",
                        "poor",
                    ])
                ),
                name="valid_prior_academic_standing",
            ),
        ),
    ]
