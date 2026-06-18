# farms/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("", views.farmer_dashboard, name="farmer_dashboard"),

    # ADD THIS LINE
    path("dashboard/", views.farmer_dashboard, name="farmer_dashboard_alias"),

    # Farms
    path("farms/", views.farm_list, name="farm_list"),
    path("farms/create/", views.farm_create, name="farm_create"),
    path("farms/<uuid:pk>/", views.farm_detail, name="farm_detail"),
    path("farms/<uuid:pk>/edit/", views.farm_update, name="farm_update"),

    # Farm Projects
    path("projects/", views.project_list, name="project_list"),
    path("projects/create/", views.project_create, name="project_create"),
    path("farms/<uuid:farm_pk>/projects/create/", views.project_create, name="farm_project_create"),
    path("projects/<uuid:pk>/edit/", views.project_update, name="project_update"),

    # Harvests
    path("harvests/", views.harvest_list, name="harvest_list"),
    path("harvests/create/", views.harvest_create, name="harvest_create"),
    path("harvests/<uuid:pk>/edit/", views.harvest_update, name="harvest_update"),

    # Expenses
    path("expenses/", views.expense_list, name="expense_list"),
    path("expenses/create/", views.expense_create, name="expense_create"),
    path("expenses/<uuid:pk>/edit/", views.expense_update, name="expense_update"),

    # Sales
    path("sales/", views.sale_list, name="sale_list"),
    path("sales/create/", views.sale_create, name="sale_create"),
    path("sales/<uuid:pk>/edit/", views.sale_update, name="sale_update"),

    # Profit Summary
    path("profit/", views.profit_summary, name="profit_summary"),
]