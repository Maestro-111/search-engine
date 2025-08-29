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
        ("marketing", "Marketing"),
        ("finance", "Finance"),
        ("designer", "Designer"),
        ("healthcare", "Healthcare"),
        ("educator", "Educator"),
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


class TrainingData(models.Model):
    user = models.ForeignKey(
        SyntheticUser, on_delete=models.CASCADE, related_name="training_data"
    )
    query = models.TextField()
    entity = models.JSONField()  # Stores the entity dict
    doc_url = models.URLField(max_length=500, blank=True)
    doc_title = models.CharField(max_length=500)
    relevance_score = models.FloatField()
    rank = models.IntegerField()

    # Denormalized fields for easier querying
    user_persona = models.CharField(max_length=50)
    user_expertise = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "query"]),
            models.Index(fields=["relevance_score"]),
            models.Index(fields=["rank"]),
        ]
        ordering = ["user", "query", "rank"]

    def __str__(self):
        return f"{self.user.name} - {self.query[:50]} - Rank: {self.rank}"
