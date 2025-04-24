from django.urls import path
from . import views

urlpatterns = [
    path('search_wiki/', views.search, name='wikipedia_search'),
]