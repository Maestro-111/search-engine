from django.urls import path
from . import views

urlpatterns = [
    path("dota_buff_search/", views.dota_buff_search, name="dota_buff_search"),
]
