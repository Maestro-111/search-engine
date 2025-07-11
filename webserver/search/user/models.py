from django.db import models


class SyntheticUser(models.Model):

    EXPERTISE_LEVELS = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("expert", "Expert"),
    ]

    PERSONAS = [
        ("developer", "Developer"),
        ("data_scientist", "Data Scientist"),
        ("business_analyst", "Business Analyst"),
        ("researcher", "Researcher"),
        ("student", "Student"),
        ("hr", "HR"),
        ("historian", "Historian"),
    ]

    name = models.CharField(max_length=100)
    persona = models.CharField(max_length=50, choices=PERSONAS)
    expertise_level = models.CharField(max_length=20, choices=EXPERTISE_LEVELS)
    importance = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.persona}"


class UserPreference(models.Model):

    user = models.ForeignKey(
        SyntheticUser, on_delete=models.CASCADE, related_name="preferences"
    )
    preference_type = models.CharField(max_length=50)
    preference_value = models.CharField(max_length=200)
    weight = models.FloatField(default=100)

    class Meta:
        unique_together = ["user", "preference_type", "preference_value"]


# class QueryTemplate(models.Model):
#     template = models.CharField(max_length=500)
#     persona = models.CharField(max_length=50, choices=SyntheticUser.PERSONAS)
#     complexity = models.CharField(max_length=20, choices=SyntheticUser.EXPERTISE_LEVELS)
#     placeholders = models.JSONField(default=dict)  # Store placeholder options
#
#     def __str__(self):
#         return f"{self.template} ({self.persona})"
