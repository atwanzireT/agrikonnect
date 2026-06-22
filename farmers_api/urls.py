from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AccountRegistrationAPIView,
    FarmerLoginAPIView,
    FarmerLogoutAPIView,
    FarmerProfileAPIView,
    FarmerDetailsAPIView,
    FarmerAppDataAPIView,
    FarmerProductDetailAPIView,
    FarmerDashboardAPIView,
    FarmerOfflineSyncAPIView,
    FarmViewSet,
    FarmActivityViewSet,
    HarvestRecordViewSet,
    FarmExpenseViewSet,
    SalesRecordViewSet,
    FarmProjectViewSet,
    ProductionBatchViewSet,
    ProjectPlannedActivityViewSet,
    ProjectInputRecordViewSet,
    ProjectRevenueRecordViewSet,
    ProjectPlannerAPIView,
    ProfitComparisonAPIView,
    ProjectInputTrendsAPIView,
    MarketplaceMapAPIView,
    ProduceListingViewSet,
    OpenProduceListingViewSet,
    OpenBuyerRequestViewSet,
    ListingInquiryViewSet,
    MarketplacePurchaseViewSet,
)

router = DefaultRouter()
router.register("farms", FarmViewSet, basename="api-farms")
router.register("activities", FarmActivityViewSet, basename="api-activities")
router.register("harvests", HarvestRecordViewSet, basename="api-harvests")
router.register("expenses", FarmExpenseViewSet, basename="api-expenses")
router.register("sales", SalesRecordViewSet, basename="api-sales")
router.register("projects", FarmProjectViewSet, basename="api-projects")
router.register("batches", ProductionBatchViewSet, basename="api-batches")
router.register("project-plans", ProjectPlannedActivityViewSet, basename="api-project-plans")
router.register("project-inputs", ProjectInputRecordViewSet, basename="api-project-inputs")
router.register("project-revenues", ProjectRevenueRecordViewSet, basename="api-project-revenues")
router.register("listings", ProduceListingViewSet, basename="api-listings")
router.register("my-listings", ProduceListingViewSet, basename="api-my-listings")
router.register("products", OpenProduceListingViewSet, basename="api-products")
router.register("buyer-requests", OpenBuyerRequestViewSet, basename="api-buyer-requests")
router.register("listing-inquiries", ListingInquiryViewSet, basename="api-listing-inquiries")
router.register("purchases", MarketplacePurchaseViewSet, basename="api-purchases")

urlpatterns = [
    path("register/", AccountRegistrationAPIView.as_view(), name="farmer-api-register"),
    path("login/", FarmerLoginAPIView.as_view(), name="farmer-api-login"),
    path("logout/", FarmerLogoutAPIView.as_view(), name="farmer-api-logout"),
    path("me/", FarmerProfileAPIView.as_view(), name="farmer-api-me"),
    path("details/", FarmerDetailsAPIView.as_view(), name="farmer-api-details"),
    path("app-data/", FarmerAppDataAPIView.as_view(), name="farmer-api-app-data"),
    path("product/<uuid:pk>/", FarmerProductDetailAPIView.as_view(), name="farmer-api-product-detail"),
    path("dashboard/", FarmerDashboardAPIView.as_view(), name="farmer-api-dashboard"),
    path("sync/", FarmerOfflineSyncAPIView.as_view(), name="farmer-api-sync"),
    path("planner/", ProjectPlannerAPIView.as_view(), name="farmer-api-planner"),
    path("profit-compare/", ProfitComparisonAPIView.as_view(), name="farmer-api-profit-compare"),
    path("input-trends/", ProjectInputTrendsAPIView.as_view(), name="farmer-api-input-trends"),
    path("market-map/", MarketplaceMapAPIView.as_view(), name="farmer-api-market-map"),
    path("", include(router.urls)),
]
