from django.contrib import admin

from .models import (
    ProduceListing,
    ProduceListingImage,
    ListingInquiry,
    BuyerRequest,
    BuyerRequestImage,
)


class ProduceListingImageInline(admin.TabularInline):
    model = ProduceListingImage
    extra = 1
    fields = ("image", "uploaded_by", "is_primary", "sort_order", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("uploaded_by",)


class BuyerRequestImageInline(admin.TabularInline):
    model = BuyerRequestImage
    extra = 1
    fields = ("image", "uploaded_by", "is_primary", "sort_order", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("uploaded_by",)


@admin.register(ProduceListing)
class ProduceListingAdmin(admin.ModelAdmin):
    list_display = (
        "crop_name",
        "farmer",
        "farm",
        "quantity",
        "unit",
        "expected_price",
        "district",
        "status",
        "available_from",
        "created_at",
    )
    list_filter = (
        "status",
        "crop_name",
        "district",
        "available_from",
        "created_at",
    )
    search_fields = (
        "crop_name",
        "variety",
        "quality",
        "district",
        "subcounty",
        "village",
        "farmer__full_name",
        "farmer__phone",
        "farm__farm_name",
    )
    autocomplete_fields = ("farmer", "farm")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = [ProduceListingImageInline]
    actions = ["mark_open", "mark_closed", "mark_sold"]

    @admin.action(description="Mark selected listings as open")
    def mark_open(self, request, queryset):
        queryset.update(status="open")

    @admin.action(description="Mark selected listings as closed")
    def mark_closed(self, request, queryset):
        queryset.update(status="closed")

    @admin.action(description="Mark selected listings as sold")
    def mark_sold(self, request, queryset):
        queryset.update(status="sold")


@admin.register(ProduceListingImage)
class ProduceListingImageAdmin(admin.ModelAdmin):
    list_display = (
        "listing",
        "uploaded_by",
        "is_primary",
        "sort_order",
        "created_at",
    )
    list_filter = ("is_primary", "created_at")
    search_fields = (
        "listing__crop_name",
        "listing__farmer__full_name",
        "uploaded_by__full_name",
    )
    autocomplete_fields = ("listing", "uploaded_by")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("sort_order", "-created_at")


@admin.register(ListingInquiry)
class ListingInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "listing",
        "business_user",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "listing__crop_name",
        "listing__farmer__full_name",
        "business_user__full_name",
        "business_user__email",
        "message",
    )
    autocomplete_fields = ("listing", "business_user")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(BuyerRequest)
class BuyerRequestAdmin(admin.ModelAdmin):
    list_display = (
        "crop_name",
        "business_user",
        "quantity_needed",
        "unit",
        "min_price",
        "max_price",
        "delivery_district",
        "status",
        "date_needed",
        "created_at",
    )
    list_filter = (
        "status",
        "crop_name",
        "delivery_district",
        "date_needed",
        "created_at",
    )
    search_fields = (
        "crop_name",
        "variety",
        "delivery_district",
        "delivery_location",
        "business_user__full_name",
        "business_user__email",
        "notes",
    )
    autocomplete_fields = ("business_user",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = [BuyerRequestImageInline]
    actions = ["mark_open", "mark_matched", "mark_closed"]

    @admin.action(description="Mark selected buyer requests as open")
    def mark_open(self, request, queryset):
        queryset.update(status="open")

    @admin.action(description="Mark selected buyer requests as matched")
    def mark_matched(self, request, queryset):
        queryset.update(status="matched")

    @admin.action(description="Mark selected buyer requests as closed")
    def mark_closed(self, request, queryset):
        queryset.update(status="closed")


@admin.register(BuyerRequestImage)
class BuyerRequestImageAdmin(admin.ModelAdmin):
    list_display = (
        "buyer_request",
        "uploaded_by",
        "is_primary",
        "sort_order",
        "created_at",
    )
    list_filter = ("is_primary", "created_at")
    search_fields = (
        "buyer_request__crop_name",
        "buyer_request__business_user__full_name",
        "uploaded_by__full_name",
    )
    autocomplete_fields = ("buyer_request", "uploaded_by")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("sort_order", "-created_at")