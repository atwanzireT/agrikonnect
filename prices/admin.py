from django.contrib import admin

from .models import CompanyProductPrice, MarketPrice


@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    list_display = (
        "crop_name", "variety", "market_name", "district", "price_date",
        "min_price", "max_price", "average_price", "source_name", "entered_by",
    )
    list_filter = ("district", "market_name", "price_date", "created_at")
    search_fields = ("crop_name", "variety", "market_name", "district", "source_name", "entered_by__full_name")
    autocomplete_fields = ("entered_by",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-price_date", "-created_at")


@admin.register(CompanyProductPrice)
class CompanyProductPriceAdmin(admin.ModelAdmin):
    list_display = (
        "product_name", "variety", "company_name", "district", "unit",
        "price_per_unit", "minimum_quantity", "price_date", "is_active", "entered_by",
    )
    list_filter = ("is_active", "unit", "district", "price_date", "created_at")
    search_fields = ("product_name", "variety", "company_name", "district", "pickup_location", "phone_number")
    autocomplete_fields = ("entered_by",)
    readonly_fields = ("id", "created_at", "updated_at")
