from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("help/", views.help_center, name="help_center"),
    path("settings/", views.settings_view, name="settings"),
]
