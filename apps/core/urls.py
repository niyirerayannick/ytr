from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("service-worker.js", views.service_worker, name="service_worker"),
    path("health/", views.health, name="health"),
    path("search/", views.search, name="search"),
]
