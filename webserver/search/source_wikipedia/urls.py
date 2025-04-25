from django.urls import path
from . import views

urlpatterns = [
    path('search_wiki/', views.search_wikipedia, name='search_wikipedia'),
    path('crawl_wiki/', views.crawl_wikipedia, name='crawl_wikipedia'),
]