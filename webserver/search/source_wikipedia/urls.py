from django.urls import path
from . import views

urlpatterns = [
    path('search_wiki/', views.search_wikipedia, name='search_wikipedia'),
]