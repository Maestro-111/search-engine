from django.db import models

# models.py in your Django app
from django.db import models


class CrawlJob(models.Model):
    STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    starting_url = models.URLField()
    crawl_depth = models.IntegerField()
    max_pages = models.IntegerField()
    mongodb_collection = models.CharField(max_length=100)

    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Crawl Job {self.id} - {self.status}"