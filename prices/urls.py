from django.urls import path
from . import views

app_name = "prices"

urlpatterns = [
    path("", views.market_price_list, name="market_price_list"),
    path("create/", views.market_price_create, name="market_price_create"),
    path("company-compare/", views.company_price_compare, name="company_price_compare"),
    path("company-compare/create/", views.company_price_create, name="company_price_create"),
]
