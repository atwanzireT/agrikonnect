from django.urls import path
from . import views

app_name = "profiles"

urlpatterns = [
    path("farmer/", views.farmer_profile_update, name="farmer_profile_update"),
    path("business/", views.business_profile_update, name="business_profile_update"),
    path("business/documents/upload/", views.business_document_upload, name="business_document_upload"),
]