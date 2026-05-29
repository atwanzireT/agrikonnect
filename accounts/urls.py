from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.dashboard_redirect, name="dashboard_redirect"),
    path("farmer/request-otp/", views.farmer_request_otp, name="farmer_request_otp"),
    path("farmer/verify-otp/", views.farmer_verify_otp, name="farmer_verify_otp"),
    path("farmer/signup/", views.farmer_signup, name="farmer_signup"),
    path("farmer/login/", views.farmer_login, name="farmer_login"),
    path("business/signup/", views.business_signup, name="business_signup"),
    path("business/login/", views.business_login, name="business_login"),
    path("logout/", views.logout_view, name="logout"),
]