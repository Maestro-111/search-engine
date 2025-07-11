from django.db import models


class CrawlJob(models.Model):
    STATUS_CHOICES = (
        ("queued", "Queued"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    starting_url = models.URLField()
    crawl_depth = models.IntegerField()
    max_pages = models.IntegerField()

    mongodb_db = models.CharField(max_length=100, blank=True, null=True)
    mongodb_collection = models.CharField(max_length=100)
    spider_name = models.CharField(max_length=100, blank=True, null=True)

    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Crawl Job {self.id} - {self.status}"


class IndexJob(models.Model):
    STATUS_CHOICES = (
        ("queued", "Queued"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    crawl_job = models.ForeignKey(
        CrawlJob, on_delete=models.CASCADE, related_name="index_jobs"
    )
    mongodb_db = models.CharField(max_length=100)
    mongodb_collection = models.CharField(max_length=100)
    elastic_index = models.CharField(max_length=100)
    batch_size = models.IntegerField(default=100)

    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Index Job {self.id} - {self.status}"
