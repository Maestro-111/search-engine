from django.urls import path
from . import views

urlpatterns = [
    path('search_bbc/', views.search_bbc, name='search_bbc')
]