import os
from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "search.settings.local")
app = Celery("search")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.task_routes = {
    "common_utils.tasks.*": {"queue": "django"},
}

app.autodiscover_tasks()
