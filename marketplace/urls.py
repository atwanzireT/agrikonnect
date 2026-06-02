from django.urls import path
from . import views

app_name = "marketplace"

urlpatterns = [
    path("business/dashboard/", views.business_dashboard, name="business_dashboard"),

    path("listings/", views.listing_list, name="listing_list"),
    path("listings/create/", views.listing_create, name="listing_create"),
    path("listings/<uuid:pk>/", views.listing_detail, name="listing_detail"),
    path("listings/<uuid:pk>/images/upload/", views.listing_image_upload, name="listing_image_upload"),
    path("listings/<uuid:pk>/inquiry/", views.inquiry_create, name="inquiry_create"),
    path("listings/<uuid:pk>/purchase/", views.purchase_create, name="purchase_create"),

    path("buyer-requests/", views.buyer_request_list, name="buyer_request_list"),
    path("buyer-requests/create/", views.buyer_request_create, name="buyer_request_create"),
    path("buyer-requests/<uuid:pk>/images/upload/", views.buyer_request_image_upload, name="buyer_request_image_upload"),

    path("map/", views.market_map, name="market_map"),
    path("prices/", views.price_list, name="price_list"),
]