from django.urls import path
from . import views

app_name = "prices"

urlpatterns = [
    path("", views.market_price_list, name="market_price_list"),
    path("create/", views.market_price_create, name="market_price_create"),
]