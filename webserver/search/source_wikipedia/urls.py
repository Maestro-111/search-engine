from django.urls import path
from . import views

urlpatterns = [
    path("wiki_search/", views.wiki_search, name="wiki_search"),
    path("wiki_crawl/", views.wiki_crawl, name="wiki_crawl"),
    path(
        "wiki_crawl_status/<int:job_id>/",
        views.wiki_crawler_job_status,
        name="wiki_crawler_job_status",
    ),
    path(
        "wiki_remove_job/<int:job_id>/", views.wiki_remove_job, name="wiki_remove_job"
    ),
    path(
        "wiki_crawl_all_jobs/",
        views.wiki_all_crawler_jobs,
        name="wiki_all_crawler_jobs",
    ),
]
