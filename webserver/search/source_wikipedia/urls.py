from django.urls import path
from . import views

urlpatterns = [
    path('search_wiki/', views.search_wikipedia, name='search_wikipedia'),
    path('crawl_wiki/', views.crawl_wikipedia, name='crawl_wikipedia'),
    path('wiki_crawl_status/<int:job_id>/', views.crawler_job_status, name='crawler_job_status'),
    path('wiki_remove_job/<int:job_id>/', views.remove_job, name='remove_job'),
    path('wiki_crawl_all_jobs/', views.all_crawler_jobs, name='all_crawler_jobs'),
]