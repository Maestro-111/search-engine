from django.urls import path
from . import views

urlpatterns = [
    path("search_custom/", views.search_custom, name="search_custom"),
]
