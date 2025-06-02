from django.urls import path
from . import views

urlpatterns = [
    path("search_bbc/", views.search_bbc, name="bbc_search"),
    path("crawl_bbc/", views.crawl_bbc, name="bbc_crawl"),
    path(
        "bbc_crawl_status/<int:job_id>/",
        views.bbc_crawler_job_status,
        name="bbc_crawler_job_status",
    ),
    path("bbc_remove_job/<int:job_id>/", views.bbc_remove_job, name="bbc_remove_job"),
    path(
        "bbc_crawl_all_jobs/", views.bbc_all_crawler_jobs, name="bbc_all_crawler_jobs"
    ),
]
